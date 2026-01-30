# ADR-001: Migration from Country State City API to LocationIQ

## Status
**ACCEPTED** - Implemented on 2026-01-31

## Context
The application was using Country State City API for location services, but users were experiencing JavaScript errors where API endpoints returned HTML instead of JSON. The existing system had limited functionality and poor error handling.

## Decision
Migrate to LocationIQ API for comprehensive location services including:
- Dynamic country/state/city dropdowns
- Geocoding and reverse geocoding
- Enhanced search capabilities
- Better error handling and fallback data

## Rationale
1. **Reliability**: LocationIQ provides more stable API responses
2. **Features**: Comprehensive location services beyond basic dropdowns
3. **Error Handling**: Better fallback mechanisms for offline/demo mode
4. **Scalability**: Professional-grade API with proper rate limiting
5. **Documentation**: Well-documented API with clear usage patterns

## Implementation Details
- Created `services/location_service.py` with LocationIQ integration
- Added fallback data for demo/offline scenarios
- Implemented caching and error handling
- Updated access guards to allow API routes
- Added comprehensive API status endpoints

## Consequences
### Positive
- Resolved JavaScript errors in location dropdowns
- Enhanced user experience with real-time location loading
- Better error handling and fallback mechanisms
- Professional-grade location services

### Negative
- Additional API dependency and cost
- Migration effort required
- Need to manage API keys securely

## Alternatives Considered
1. **Fix existing Country State City API**: Limited functionality, poor documentation
2. **Use Google Places API**: More expensive, overkill for basic location needs
3. **Static location data**: No real-time updates, limited coverage

## Follow-up Actions
- Monitor LocationIQ API usage and costs
- Implement additional caching if needed
- Consider upgrading to paid plan for production use