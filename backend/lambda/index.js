/**
 * Sampark AI - Main Lambda Handler
 * Handles voice queries, scheme lookup, and audio generation
 */

const { DynamoDBClient } = require('@aws-sdk/client-dynamodb');
const { DynamoDBDocumentClient, GetCommand, ScanCommand, QueryCommand } = require('@aws-sdk/lib-dynamodb');
const { BedrockRuntimeClient, InvokeModelCommand } = require('@aws-sdk/client-bedrock-runtime');
const { PollyClient, SynthesizeSpeechCommand } = require('@aws-sdk/client-polly');
const { TranscribeClient, StartTranscriptionJobCommand, GetTranscriptionJobCommand } = require('@aws-sdk/client-transcribe');
const { S3Client, PutObjectCommand, GetObjectCommand } = require('@aws-sdk/client-s3');
const { getSignedUrl } = require('@aws-sdk/s3-request-presigner');

// Initialize AWS clients
const dynamoClient = new DynamoDBClient({ region: 'ap-south-1' });
const docClient = DynamoDBDocumentClient.from(dynamoClient);
const bedrockClient = new BedrockRuntimeClient({ region: 'us-east-1' }); // Bedrock availability
const pollyClient = new PollyClient({ region: 'ap-south-1' });
const transcribeClient = new TranscribeClient({ region: 'ap-south-1' });
const s3Client = new S3Client({ region: 'ap-south-1' });

// Environment variables
const SCHEMES_TABLE = process.env.SCHEMES_TABLE || 'SamparkSchemes';
const AUDIO_BUCKET = process.env.AUDIO_BUCKET || 'sampark-audio-bucket';

// CORS headers for API Gateway
const corsHeaders = {
  'Access-Control-Allow-Origin': '*',
  'Access-Control-Allow-Headers': 'Content-Type,Authorization',
  'Access-Control-Allow-Methods': 'GET,POST,OPTIONS',
  'Content-Type': 'application/json'
};

// Category keywords mapping
const CATEGORY_KEYWORDS = {
  farmer: ['kisan', 'kheti', 'farmer', 'zameen', 'fasal', 'krishi', 'agriculture', 'खेती', 'किसान'],
  student: ['student', 'padhai', 'vidya', 'school', 'college', 'education', 'scholarship', 'loan', 'पढ़ाई', 'विद्यार्थी'],
  woman: ['mahila', 'woman', 'aurat', 'mata', 'beti', 'ladki', 'ujjwala', 'gas', 'महिला', 'औरत']
};

// Bedrock prompt template (as specified in requirements)
const BEDROCK_PROMPT = `Tum Sampark AI ho.

Rules:
- Hinglish me jawab do
- Bahut simple shabd use karo
- Gaon ke aadmi jaise samjhao
- Legal ya sarkari bhaasha mat use karo
- Steps hamesha numbered me likho
- Short sentences

Goal:
User ko scheme, eligibility, documents aur steps samjhao.

Scheme Details:
{scheme_details}

User ka sawal: {user_query}

Samjhao:`;

/**
 * Main Lambda handler
 */
exports.handler = async (event) => {
  console.log('Event:', JSON.stringify(event, null, 2));
  
  // Handle CORS preflight
  if (event.httpMethod === 'OPTIONS') {
    return { statusCode: 200, headers: corsHeaders, body: '' };
  }

  const path = event.path || event.rawPath || '';
  const method = event.httpMethod || event.requestContext?.http?.method;

  try {
    // Route requests
    if (path.includes('/query') && method === 'POST') {
      return await handleVoiceQuery(event);
    }
    
    if (path.includes('/scheme/') && method === 'GET') {
      const category = path.split('/scheme/')[1];
      return await getSchemeByCategory(category);
    }
    
    if (path.includes('/transcribe') && method === 'POST') {
      return await handleTranscription(event);
    }
    
    if (path.includes('/audio/') && method === 'GET') {
      const schemeId = path.split('/audio/')[1];
      return await getSchemeAudio(schemeId);
    }
    
    if (path.includes('/health')) {
      return {
        statusCode: 200,
        headers: corsHeaders,
        body: JSON.stringify({ status: 'healthy', service: 'sampark-ai' })
      };
    }

    return {
      statusCode: 404,
      headers: corsHeaders,
      body: JSON.stringify({ error: 'Not found' })
    };

  } catch (error) {
    console.error('Lambda error:', error);
    return {
      statusCode: 500,
      headers: corsHeaders,
      body: JSON.stringify({ error: 'Internal server error', message: error.message })
    };
  }
};

/**
 * Handle voice query - main flow
 */
async function handleVoiceQuery(event) {
  const body = JSON.parse(event.body || '{}');
  const { transcript } = body;

  if (!transcript) {
    return {
      statusCode: 400,
      headers: corsHeaders,
      body: JSON.stringify({ error: 'Transcript is required' })
    };
  }

  console.log('Processing transcript:', transcript);

  // Step 1: Detect category from transcript
  const category = detectCategory(transcript);
  console.log('Detected category:', category);

  // Step 2: Get scheme from DynamoDB
  const scheme = await getSchemeFromDB(category);
  console.log('Retrieved scheme:', scheme?.scheme_id);

  // Step 3: Generate AI explanation using Bedrock
  const explanation = await generateExplanation(scheme, transcript);
  console.log('Generated explanation length:', explanation?.length);

  // Step 4: Generate audio using Polly
  const audioUrl = await generateAudio(explanation, scheme.scheme_id);
  console.log('Generated audio URL:', audioUrl ? 'Success' : 'Failed');

  return {
    statusCode: 200,
    headers: corsHeaders,
    body: JSON.stringify({
      category,
      scheme: {
        ...scheme,
        explanation
      },
      audioUrl,
      transcript
    })
  };
}

/**
 * Detect category from user input
 */
function detectCategory(transcript) {
  const text = transcript.toLowerCase();
  
  for (const [category, keywords] of Object.entries(CATEGORY_KEYWORDS)) {
    for (const keyword of keywords) {
      if (text.includes(keyword.toLowerCase())) {
        return category;
      }
    }
  }
  
  // Default to farmer if no match
  return 'farmer';
}

/**
 * Get scheme from DynamoDB
 */
async function getSchemeFromDB(category) {
  try {
    // Query by category
    const command = new ScanCommand({
      TableName: SCHEMES_TABLE,
      FilterExpression: 'category = :cat',
      ExpressionAttributeValues: {
        ':cat': category
      },
      Limit: 1
    });

    const response = await docClient.send(command);
    
    if (response.Items && response.Items.length > 0) {
      return response.Items[0];
    }

    // Return default scheme if not found in DB
    return getDefaultScheme(category);

  } catch (error) {
    console.error('DynamoDB error:', error);
    return getDefaultScheme(category);
  }
}

/**
 * Default schemes (fallback when DB unavailable)
 */
function getDefaultScheme(category) {
  const schemes = {
    farmer: {
      scheme_id: 'PM_KISAN',
      name: 'PM Kisan Samman Nidhi',
      category: 'farmer',
      eligibility: 'Chhote aur seemant kisan jo 2 hectare se kam zameen rakhte hain',
      benefit: '₹6000 har saal, 3 kisht mein ₹2000',
      documents: ['Aadhaar Card', 'Bank Account', 'Zameen ke Kagaz', 'Mobile Number'],
      steps: [
        'PM Kisan website (pmkisan.gov.in) par jao',
        'New Farmer Registration par click karo',
        'Apna Aadhaar number daalo',
        'Bank details bharo',
        'Zameen ki jaankari do',
        'Submit karo'
      ]
    },
    student: {
      scheme_id: 'PM_VIDYALAKSHMI',
      name: 'PM Vidyalakshmi Yojana',
      category: 'student',
      eligibility: 'Jo students higher education ke liye loan chahte hain',
      benefit: 'Education loan easy process se, kam interest rate',
      documents: ['Aadhaar Card', 'Admission Letter', 'Marksheet', 'Income Proof', 'Bank Account'],
      steps: [
        'Vidyalakshmi Portal par jao',
        'Register karo',
        'College select karo',
        'Loan amount daalo',
        'Documents upload karo',
        'Apply karo'
      ]
    },
    woman: {
      scheme_id: 'PM_UJJWALA',
      name: 'Pradhan Mantri Ujjwala Yojana',
      category: 'woman',
      eligibility: 'BPL parivar ki mahilayen, 18 saal se upar',
      benefit: 'Free LPG connection, ₹1600 ki subsidy',
      documents: ['Aadhaar Card', 'BPL Ration Card', 'Bank Account', 'Passport Photo'],
      steps: [
        'Nazdeeki LPG distributor ke paas jao',
        'Ujjwala form bharo',
        'Documents attach karo',
        'KYC complete karo',
        'Connection mil jayega'
      ]
    }
  };

  return schemes[category] || schemes.farmer;
}

/**
 * Generate AI explanation using Amazon Bedrock
 */
async function generateExplanation(scheme, userQuery) {
  try {
    const schemeDetails = `
Yojana: ${scheme.name}
Faayda: ${scheme.benefit}
Eligibility: ${scheme.eligibility}
Documents: ${scheme.documents.join(', ')}
Steps: ${scheme.steps.map((s, i) => `${i + 1}. ${s}`).join(' ')}
    `;

    const prompt = BEDROCK_PROMPT
      .replace('{scheme_details}', schemeDetails)
      .replace('{user_query}', userQuery);

    const command = new InvokeModelCommand({
      modelId: 'anthropic.claude-3-haiku-20240307-v1:0',
      contentType: 'application/json',
      accept: 'application/json',
      body: JSON.stringify({
        anthropic_version: 'bedrock-2023-05-31',
        max_tokens: 500,
        messages: [
          {
            role: 'user',
            content: prompt
          }
        ]
      })
    });

    const response = await bedrockClient.send(command);
    const responseBody = JSON.parse(new TextDecoder().decode(response.body));
    
    return responseBody.content[0].text;

  } catch (error) {
    console.error('Bedrock error:', error);
    
    // Fallback explanation
    return `
${scheme.name} ek bahut acchi yojana hai.

Isme aapko milega: ${scheme.benefit}

Kaun apply kar sakta hai: ${scheme.eligibility}

Documents rakhein: ${scheme.documents.join(', ')}

Apply kaise karein:
${scheme.steps.map((s, i) => `${i + 1}. ${s}`).join('\n')}
    `.trim();
  }
}

/**
 * Generate audio using Amazon Polly
 */
async function generateAudio(text, schemeId) {
  try {
    const command = new SynthesizeSpeechCommand({
      Engine: 'neural',
      LanguageCode: 'hi-IN',
      OutputFormat: 'mp3',
      Text: text,
      TextType: 'text',
      VoiceId: 'Kajal' // Hindi neural voice
    });

    const response = await pollyClient.send(command);
    
    // Upload to S3
    const audioKey = `audio/${schemeId}_${Date.now()}.mp3`;
    const audioStream = response.AudioStream;
    
    // Convert stream to buffer
    const chunks = [];
    for await (const chunk of audioStream) {
      chunks.push(chunk);
    }
    const audioBuffer = Buffer.concat(chunks);

    await s3Client.send(new PutObjectCommand({
      Bucket: AUDIO_BUCKET,
      Key: audioKey,
      Body: audioBuffer,
      ContentType: 'audio/mpeg'
    }));

    // Generate presigned URL
    const signedUrl = await getSignedUrl(
      s3Client,
      new GetObjectCommand({
        Bucket: AUDIO_BUCKET,
        Key: audioKey
      }),
      { expiresIn: 3600 } // 1 hour
    );

    return signedUrl;

  } catch (error) {
    console.error('Polly/S3 error:', error);
    return null; // Frontend will fallback to Web Speech API
  }
}

/**
 * Get scheme by category (GET endpoint)
 */
async function getSchemeByCategory(category) {
  const scheme = await getSchemeFromDB(category);
  
  return {
    statusCode: 200,
    headers: corsHeaders,
    body: JSON.stringify(scheme)
  };
}

/**
 * Handle audio transcription using Amazon Transcribe
 */
async function handleTranscription(event) {
  try {
    // For demo, we'll return a simulated transcript
    // In production, this would:
    // 1. Upload audio to S3
    // 2. Start Transcribe job
    // 3. Wait for completion
    // 4. Return transcript

    const body = JSON.parse(event.body || '{}');
    
    // Simulated response for demo
    return {
      statusCode: 200,
      headers: corsHeaders,
      body: JSON.stringify({
        transcript: 'kisan yojana ke baare mein batao',
        confidence: 0.95
      })
    };

  } catch (error) {
    console.error('Transcription error:', error);
    return {
      statusCode: 500,
      headers: corsHeaders,
      body: JSON.stringify({ error: 'Transcription failed' })
    };
  }
}

/**
 * Get pre-generated audio for a scheme
 */
async function getSchemeAudio(schemeId) {
  try {
    const audioKey = `audio/${schemeId}.mp3`;
    
    const signedUrl = await getSignedUrl(
      s3Client,
      new GetObjectCommand({
        Bucket: AUDIO_BUCKET,
        Key: audioKey
      }),
      { expiresIn: 3600 }
    );

    return {
      statusCode: 200,
      headers: corsHeaders,
      body: JSON.stringify({ audioUrl: signedUrl })
    };

  } catch (error) {
    console.error('Audio fetch error:', error);
    return {
      statusCode: 404,
      headers: corsHeaders,
      body: JSON.stringify({ error: 'Audio not found' })
    };
  }
}
