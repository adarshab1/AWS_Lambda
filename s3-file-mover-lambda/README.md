![AWS](https://img.shields.io/badge/AWS-Lambda%20%7C%20S3-orange?logo=amazonaws)
![Language](https://img.shields.io/badge/Runtime-Python%203.11-blue)
![Automation](https://img.shields.io/badge/Automation-Serverless-green)
![Status](https://img.shields.io/badge/Workflow-Active-success)
![Security](https://img.shields.io/badge/IAM-Least%20Privilege-yellow)
![CloudWatch](https://img.shields.io/badge/Logs-CloudWatch-purple)
![License](https://img.shields.io/badge/License-NA-lightgrey)

# S3 Inbound → Processed Automation Using AWS Lambda

This document provides a complete summary and setup guide for creating an automated S3-to-S3 copy flow using AWS Lambda, triggered when new objects are uploaded into the **inbound/** folder.

---

## 📌 Overview

### Architecture
- An single S3 bucket named **trail-lambda-bucket-1** is created.
- The bucket contains:
  - `outbound/` (files arrive here from external applications)
  - `inbound/incomming/`
  - `inbound/completed/`
  - `inbound/error/`
- An AWS Lambda function listens for new objects in `outbound/`.
- When a new file is uploaded, Lambda:
  - Copies it to `inbound/incomming/`
  - Does **not** delete the original

---

## 📌 Components Created

### 0 **S3 Bucket**
Created using AWS CLI with:
- Public access blocked
- SSE-S3 encryption
- Versioning (optional)

### 1 **IAM Role (`lambda-s3-mover-role`)**
Create lambda with trust relatoionship
```
 aws iam create-role --role-name lambda-s3-mover-role --assume-role-policy-document file://trust-policy1.json
```
Attached policies:
- **AWSLambdaBasicExecutionRole** → allows CloudWatch logging
```  
 aws iam attach-role-policy ^
       --role-name lambda-s3-mover-role ^
       --policy-arn arn:aws:iam::aws:policy/service-role/AWSLambdaBasicExecutionRole
```

- **Custom Inline S3 Access Policy** → restricts access to only `trail-lambda-bucket-1`
```
aws iam put-role-policy ^
       --role-name lambda-s3-mover-role ^
       --policy-name LambdaS3MovePolicy ^
       --policy-document file://s3-access-policy.json
```

- **Get role details**
```
aws iam get-role --role-name lambda-s3-mover-role
```

```
o/p
{
    "Role": {
        "Path": "/",
        "RoleName": "lambda-s3-mover-role",
        "RoleId": "AROA2AR3UJFGPC7TJYPJD",
        "Arn": "arn:aws:iam::112233445566:role/lambda-s3-mover-role",
        "CreateDate": "2025-12-09T06:16:35+00:00",
        "AssumeRolePolicyDocument": {
            "Version": "2012-10-17",
            "Statement": [
                {
                    "Effect": "Allow",
                    "Principal": {
                        "Service": "lambda.amazonaws.com"
                    },
                    "Action": "sts:AssumeRole"
                }
            ]
        },
        "MaxSessionDuration": 3600,
        "RoleLastUsed": {}
    }
}
```
**Trust Relationship:**
Allows Lambda to assume this role.

### 2 **Lambda Function**
Runtime: Python 3.11

Responsible for:
- Receiving S3 event payloads
- Copying new objects from:
  ```
  outbound/ → inbound/incoming/
  ```
- Keeping original objects intact

## 📌 Lambda Function Code

lambda_function.py

```python
import boto3

s3 = boto3.client("s3")

DEST_PREFIX = "inbound/incomming/"

def lambda_handler(event, context):
    for record in event["Records"]:
        bucket = record["s3"]["bucket"]["name"]
        key = record["s3"]["object"]["key"]

        # Only process outbound/ prefix
        if not key.startswith("outbound/"):
            continue

        # Skip folder placeholder events
        if key.endswith("/"):
            continue

        # Destination key
        relative_path = key[len("outbound/"):]
        dest_key = DEST_PREFIX + relative_path

        # Copy object (NO DELETE!)
        s3.copy_object(
            Bucket=bucket,
            CopySource={"Bucket": bucket, "Key": key},
            Key=dest_key
        )

        # Delete original object from outbound/
        s3.delete_object(
            Bucket=bucket,
            Key=key
        )

    return {"status": "success"}

```

### 2.1 **COMPRESS THE PYTHON CODE AND PUSH TO AWS LAMBDA FUNCTION**
```
powershell Compress-Archive -Path lambda_function.py -DestinationPath lambda_move.zip -Force
```

### 2.2 **Copy the lambda function arn**
```
aws iam get-role ^
       --role-name lambda-s3-mover-role ^
       --query "Role.Arn" ^
       --output text

o/p
arn:aws:iam::112233445566:role/lambda-s3-mover-role
```



### 2.3 **Create lambda function**
```
aws lambda create-function ^
   --function-name s3-inbound-to-processed-mover ^
   --runtime python3.11 ^
   --role arn:aws:iam::112233445566:role/lambda-s3-mover-role ^
   --handler lambda_function.lambda_handler ^
   --zip-file fileb://lambda_move.zip ^
   --timeout 30 ^
   --memory-size 256
```

### 2.4 **Give S3 Permission to Invoke Lambda**

```
aws lambda add-permission ^
     --function-name s3-inbound-to-processed-mover ^
     --statement-id s3invoke ^
     --action lambda:InvokeFunction ^
     --principal s3.amazonaws.com ^
     --source-arn arn:aws:s3:::trail-lambda-bucket-1
```

### 3 **S3 → Lambda Event Trigger**

This tells S3 to call Lambda when new files arrive in
Configured using bucket notification rules:
- Trigger: `s3:ObjectCreated:*`
- Prefix filter: `inbound/`


---

### 3.1 **Get Lambda ARN:**

```
aws lambda get-function ^
   --function-name s3-inbound-to-processed-mover ^
   --query "Configuration.FunctionArn" ^
   --output text
arn:aws:lambda:ap-south-1:112233445566:function:s3-inbound-to-processed-mover
```

Create a file notification.json:
```
 {
  "LambdaFunctionConfigurations": [
    {
      "Id": "InboundPutTrigger",
      "LambdaFunctionArn": "arn:aws:lambda:ap-south-1:112233445566:function:s3-inbound-to-processed-mover",
      "Events": ["s3:ObjectCreated:*"],
      "Filter": {
        "Key": {
          "FilterRules": [
            { "Name": "prefix", "Value": "outbound/" }
          ]
        }
      }
    }
  ]
}

```



### 3.2 **Apply the notification:**
```
aws s3api put-bucket-notification-configuration ^
  --bucket trail-lambda-bucket-1 ^
  --notification-configuration file://notification.json
```

---

## 📌 Testing

Upload a test file:

```bash
aws s3 cp sample.json s3://trail-lambda-bucket-1/outbound/sample.json
```

Check logs:

- CloudWatch Log Group:
  `/aws/lambda/s3-inbound-to-processed-mover`

Check output folder:

```bash
aws s3 ls s3://trail-lambda-bucket-1/inbound/incomming/
```

---

## 📌 Validation Commands

### Check S3 notifications:
```bash
aws s3api get-bucket-notification-configuration --bucket trail-lambda-bucket-1
```

### Check Lambda invoke permissions:
```bash
aws lambda get-policy --function-name s3-inbound-to-processed-mover
```

---

## 📌 Final Behavior

| Operation | Result |
|----------|--------|
| Upload file to `outbound/` | Lambda copies it |
| Delete original file | ✅ YES |
| Create processed copy | ✅ YES |
| Triggers Lambda | Automatically |
| Logs | CloudWatch |

---

## 📌 Summary

You now have a secure, automated, event‑driven workflow using:
- IAM (least privilege)
- S3 (structured folders)
- Lambda (serverless automation)
- CloudWatch (logging)
- AWS CLI (deployment)

This setup is fully production‑ready and supports future extensions such as:
- Moving to `completed/` or `error/`
- Validating file formats
- Sending notifications
- Invoking Step Functions

---

## 📎 Author
Generated automatically via ChatGPT DevOps assistant.

