# AWS SES Setup Guide for CIFIX LEARN

This guide will help you set up AWS Simple Email Service (SES) for sending emails in the CIFIX LEARN platform.

## Prerequisites

1. AWS Account with appropriate permissions
2. Access to AWS Console
3. Domain or email address to verify

## Step 1: Create AWS Account & IAM User

1. **Create AWS Account** (if you don't have one)
   - Go to https://aws.amazon.com/
   - Sign up for an AWS account

2. **Create IAM User for SES**
   - Go to AWS IAM Console
   - Click "Users" → "Create user"
   - Username: `cifix-learn-ses-user`
   - Access type: Programmatic access
   - Attach policy: `AmazonSESFullAccess`
   - Save the **Access Key ID** and **Secret Access Key**

## Step 2: Configure AWS SES

1. **Go to AWS SES Console**
   - Navigate to AWS SES service
   - Select your preferred region (e.g., us-east-1)

2. **Verify Email Address**
   - Go to "Verified identities"
   - Click "Create identity"
   - Choose "Email address"
   - Enter your email (e.g., noreply@cifixlearn.com)
   - Check your email and click the verification link

3. **Request Production Access** (if needed)
   - By default, SES is in sandbox mode
   - Go to "Account dashboard"
   - Click "Request production access"
   - Fill out the form explaining your use case

## Step 3: Update Environment Variables

Fill in your `.env` file with the following information:

```env
# AWS SES Configuration
AWS_REGION=us-east-1
AWS_ACCESS_KEY_ID=your_access_key_here
AWS_SECRET_ACCESS_KEY=your_secret_key_here

# Email Settings
SES_SOURCE_EMAIL=noreply@cifixlearn.com
SES_REPLY_TO_EMAIL=support@cifixlearn.com
```

## Step 4: Domain Verification (Recommended)

For production use, verify your domain:

1. **Add Domain**
   - Go to "Verified identities"
   - Click "Create identity"
   - Choose "Domain"
   - Enter your domain (e.g., cifixlearn.com)

2. **Configure DNS Records**
   - AWS will provide DNS records
   - Add these records to your domain's DNS settings
   - Wait for verification (can take up to 72 hours)

## Step 5: Configure Email Templates (Optional)

1. **Create Templates in SES**
   - Go to "Configuration" → "Email templates"
   - Create templates for:
     - Email verification
     - Welcome email
     - Password reset

## Step 6: Set Up Configuration Set (Optional)

1. **Create Configuration Set**
   - Go to "Configuration" → "Configuration sets"
   - Create a new configuration set: `cifix-learn-emails`
   - Add event destinations for tracking

## Step 7: Test Email Sending

Use the email service in your application:

```javascript
const emailService = new EmailService();
await emailService.sendVerificationEmail(
    'test@example.com',
    '123456',
    'Test Student'
);
```

## Important Security Notes

1. **Never commit credentials to version control**
   - The `.env` file is in `.gitignore`
   - Use environment variables in production

2. **Use least privilege access**
   - Only grant necessary SES permissions
   - Consider using IAM roles in production

3. **Monitor usage and costs**
   - Set up billing alerts
   - Monitor SES sending statistics

## Sending Limits

- **Sandbox mode**: 200 emails per 24 hours, 1 email per second
- **Production mode**: Higher limits (request based on use case)

## Cost Information

- **Free tier**: 62,000 emails per month when called from EC2
- **After free tier**: $0.10 per 1,000 emails

## Troubleshooting

### Common Issues:

1. **Email not sending**
   - Check if email is verified in SES
   - Verify AWS credentials
   - Check AWS region settings

2. **Emails going to spam**
   - Set up SPF, DKIM, and DMARC records
   - Use verified domain
   - Monitor reputation

3. **Rate limiting**
   - Check sending limits in SES console
   - Request limit increase if needed

### Useful AWS CLI Commands:

```bash
# List verified identities
aws ses list-verified-email-addresses

# Send test email
aws ses send-email --source noreply@cifixlearn.com --destination ToAddresses=test@example.com --message Subject={Data="Test"},Body={Text={Data="Test message"}}

# Check sending statistics
aws ses get-send-statistics
```

## Support

For AWS SES support:
- AWS Documentation: https://docs.aws.amazon.com/ses/
- AWS Support: https://aws.amazon.com/support/

For CIFIX LEARN specific issues:
- Contact: support@cifixlearn.com