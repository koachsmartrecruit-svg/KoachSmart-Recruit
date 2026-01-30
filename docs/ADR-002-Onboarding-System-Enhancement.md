# ADR-002: Enhanced 3-Step Onboarding System with Mandatory Completion

## Status
**ACCEPTED** - Implemented on 2026-01-31

## Context
The existing onboarding system was optional and incomplete, leading to:
- Coaches accessing features without proper profile setup
- Poor job matching due to incomplete profiles
- Inconsistent user experience
- Low profile completion rates

## Decision
Implement a comprehensive 3-step mandatory onboarding system with:
1. **Stage 1**: Basic information, phone/email verification, language proficiency
2. **Stage 2**: Location details, job type preferences, conditional range fields
3. **Stage 3**: Education, professional certifications, document uploads

## Rationale
1. **Data Quality**: Ensures complete profiles for better job matching
2. **User Experience**: Guided process with clear progress indicators
3. **Engagement**: Gamification with badges and coin rewards
4. **Business Value**: Higher quality profiles lead to better matches

## Implementation Details
### Middleware Enforcement
- `onboarding_guard.py` blocks access to protected routes
- Redirects incomplete users to onboarding flow
- Allows API routes and public endpoints

### Progress Tracking
- `onboarding_step` field tracks current progress
- `onboarding_completed` boolean for completion status
- Real-time progress calculation and display

### Reward System
- Orange Badge: Basic verification (100 coins)
- Purple Badge: Location setup (200 coins)
- Blue Verified Badge: Full completion (500 coins)

### Enhanced Features
- Language proficiency levels (Basic/Intermediate/Fluent)
- Conditional range fields (only for part-time/full-time jobs)
- Dynamic form validation and error handling

## Consequences
### Positive
- 100% profile completion for active users
- Better job matching accuracy
- Improved user engagement through gamification
- Consistent user experience

### Negative
- Additional friction for new users
- More complex onboarding flow
- Potential user drop-off at early stages

## Alternatives Considered
1. **Optional onboarding**: Low completion rates, poor data quality
2. **Single-step onboarding**: Overwhelming for users, high abandonment
3. **Progressive disclosure**: Considered but 3-step approach provides better UX

## Follow-up Actions
- Monitor onboarding completion rates
- A/B test reward amounts for optimization
- Add analytics to identify drop-off points
- Consider onboarding flow improvements based on user feedback