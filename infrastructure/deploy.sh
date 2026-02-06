#!/bin/bash

# Sampark AI Deployment Script
# Prerequisites: AWS CLI, AWS SAM CLI, Node.js

set -e

STACK_NAME="sampark-ai"
REGION="ap-south-1"
STAGE="prod"

echo "========================================"
echo "  Sampark AI - Deployment Script"
echo "========================================"
echo ""

# Step 1: Install Lambda dependencies
echo "Step 1: Installing Lambda dependencies..."
cd ../backend/lambda
npm install --production
cd ../../infrastructure

# Step 2: Build SAM application
echo ""
echo "Step 2: Building SAM application..."
sam build --template-file template.yaml

# Step 3: Deploy to AWS
echo ""
echo "Step 3: Deploying to AWS..."
sam deploy \
    --stack-name $STACK_NAME \
    --region $REGION \
    --parameter-overrides Stage=$STAGE \
    --capabilities CAPABILITY_IAM \
    --resolve-s3 \
    --no-confirm-changeset

# Step 4: Get outputs
echo ""
echo "Step 4: Getting deployment outputs..."
API_URL=$(aws cloudformation describe-stacks \
    --stack-name $STACK_NAME \
    --region $REGION \
    --query "Stacks[0].Outputs[?OutputKey=='ApiUrl'].OutputValue" \
    --output text)

FRONTEND_BUCKET=$(aws cloudformation describe-stacks \
    --stack-name $STACK_NAME \
    --region $REGION \
    --query "Stacks[0].Outputs[?OutputKey=='FrontendBucket'].OutputValue" \
    --output text)

FRONTEND_URL=$(aws cloudformation describe-stacks \
    --stack-name $STACK_NAME \
    --region $REGION \
    --query "Stacks[0].Outputs[?OutputKey=='FrontendUrl'].OutputValue" \
    --output text)

# Step 5: Build and deploy frontend
echo ""
echo "Step 5: Building frontend..."
cd ../frontend

# Create .env file with API URL
echo "VITE_API_URL=$API_URL" > .env

npm install
npm run build

# Step 6: Upload frontend to S3
echo ""
echo "Step 6: Uploading frontend to S3..."
aws s3 sync dist/ s3://$FRONTEND_BUCKET/ \
    --delete \
    --region $REGION

# Step 7: Seed DynamoDB (if needed)
echo ""
echo "Step 7: Seeding DynamoDB..."
cd ../backend/dynamodb
chmod +x create-table.sh
# Uncomment to seed data (only run once)
# ./create-table.sh

echo ""
echo "========================================"
echo "  Deployment Complete!"
echo "========================================"
echo ""
echo "API URL: $API_URL"
echo "Frontend URL: $FRONTEND_URL"
echo ""
echo "Test the API:"
echo "  curl $API_URL/health"
echo ""
echo "Open the app:"
echo "  $FRONTEND_URL"
echo ""
