# IAM User Access to Specific S3 Bucket

![AWS](https://img.shields.io/badge/AWS-IAM-orange?logo=amazonaws)
![S3](https://img.shields.io/badge/AWS-S3-blue?logo=amazonaws)
![Status](https://img.shields.io/badge/Access-Restricted-green)
![License](https://img.shields.io/badge/License-NA-lightgrey)

This repository contains documentation and policy files for creating an IAM user with restricted access to a single S3 bucket:

`trail-lambda-bucket-1`

The IAM user will have **read, write, list, and delete permissions** only for this bucket.

---

## 📁 Files Included

```
s3-bucket-access.json     # IAM Policy with S3 permissions for one bucket
README.md                 # This documentation
```

---

# 🔐 Step 1: Create IAM User

```sh
aws iam create-user --user-name s3-external-app
```

---

# 📜 Step 2: Create IAM Policy
Create s3-bucket-access.json:

```
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": [
        "s3:PutObject",
        "s3:GetObject",
        "s3:DeleteObject",
        "s3:ListBucket"
      ],
      "Resource": [
        "arn:aws:s3:::trail-lambda-bucket-1",
        "arn:aws:s3:::trail-lambda-bucket-1/*"
      ]
    }
  ]
}

```

Create policy in aws using above file
```sh
aws iam create-policy \
  --policy-name s3-trail-lambda-bucket-1-access \
  --policy-document file://s3-bucket-access.json
```

---

# 🔗 Step 3: Attach Policy to IAM User


```sh
aws iam attach-user-policy \
  --user-name s3-external-app \
  --policy-arn arn:aws:iam::112233445566:policy/s3-trail-lambda-bucket-1-access
```

---

# 🔑 Step 4: Create Access Key for the User

```sh
aws iam create-access-key --user-name s3-external-app
```

---


---

# 🧪 Testing Access

```sh
aws s3 cp test.txt s3://trail-lambda-bucket-1/ --profile s3-external-app
aws s3 ls s3://trail-lambda-bucket-1/ --profile s3-external-app
aws s3 rm s3://trail-lambda-bucket-1/test.txt --profile s3-external-app
```

---

# ✔ Summary

| Permission | Applied To |
|-----------|-------------|
| Read       | trail-lambda-bucket-1 |
| Write      | trail-lambda-bucket-1 |
| Delete     | trail-lambda-bucket-1 |
| List       | trail-lambda-bucket-1 |

Only this S3 bucket is accessible. No other AWS services are permitted.

---
