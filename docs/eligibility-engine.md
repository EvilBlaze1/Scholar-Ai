# Scholar AI - Eligibility Engine

## Purpose

The eligibility engine compares a student's profile against a scholarship's eligibility requirements.

## Evaluation Status

- PASS
- FAIL
- UNKNOWN

## Overall Eligibility

- ELIGIBLE
- INELIGIBLE
- NEEDS_VERIFICATION

## Evaluation Rules

### Income

Student income must satisfy the scholarship's income limits.

### Category

Student category must be included in the scholarship's allowed categories.

### State

Student state or domicile must satisfy the scholarship's location requirements.

### Education

Student education level must be supported by the scholarship.

### Course

Student course must be supported by the scholarship.

### Score

Student score must satisfy the scholarship's minimum score requirement.

### Age

Student age must fall within the scholarship's allowed age range.

### Gender

Student gender must satisfy the scholarship's gender requirements.

### Disability

Student disability status must satisfy the scholarship's disability requirements.

## Decision Logic

- If every required rule passes → ELIGIBLE
- If any required rule fails → INELIGIBLE
- If no required rule fails but one or more required values are unknown → NEEDS_VERIFICATION

## AI Responsibility

AI may explain eligibility results and provide personalized scholarship recommendations.

AI must not independently determine final eligibility.