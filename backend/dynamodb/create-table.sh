#!/bin/bash

# Create DynamoDB table for Sampark AI Schemes
# Run this script with AWS CLI configured

TABLE_NAME="SamparkSchemes"
REGION="ap-south-1"

echo "Creating DynamoDB table: $TABLE_NAME"

aws dynamodb create-table \
    --table-name $TABLE_NAME \
    --attribute-definitions \
        AttributeName=scheme_id,AttributeType=S \
        AttributeName=category,AttributeType=S \
    --key-schema \
        AttributeName=scheme_id,KeyType=HASH \
    --global-secondary-indexes \
        "[{
            \"IndexName\": \"category-index\",
            \"KeySchema\": [{\"AttributeName\":\"category\",\"KeyType\":\"HASH\"}],
            \"Projection\": {\"ProjectionType\":\"ALL\"},
            \"ProvisionedThroughput\": {\"ReadCapacityUnits\":5,\"WriteCapacityUnits\":5}
        }]" \
    --provisioned-throughput \
        ReadCapacityUnits=5,WriteCapacityUnits=5 \
    --region $REGION

echo "Waiting for table to be active..."
aws dynamodb wait table-exists --table-name $TABLE_NAME --region $REGION

echo "Table created successfully!"
echo ""
echo "Now seeding data..."

# Seed data using batch write
aws dynamodb batch-write-item \
    --request-items file://seed-data.json \
    --region $REGION

echo "Data seeded successfully!"
echo ""
echo "Verifying data..."
aws dynamodb scan --table-name $TABLE_NAME --region $REGION --select COUNT
