# KoachSmart - Remaining Features to Complete

## 🔄 Phase 2: Onboarding Enforcement (Next Priority)

### Core Requirements
- **Mandatory Onboarding:** No profile access until 3-step onboarding complete
- **Onboarding Process:** 3 steps with 200 coins + Orange badge reward
- **Job Application Block:** Cannot apply for jobs until onboarding complete
- **Progress Tracking:** Track onboarding completion status

### Implementation Needed

#### 1. Onboarding Middleware
- **File:** `core/onboarding_guard.py`
- **Purpose:** Block access to profile/jobs until onboarding complete
- **Routes to protect:** Profile edit, job applications, coach dashboard

#### 2. Onboarding Progress Tracking
- **Update:** `models/user.py` (already has onboarding fields)
- **Add:** Progress tracking methods
- **Add:** Coin and badge reward system

#### 3. Onboarding Routes Update
- **Update:** `routes/onboarding_routes.py`
- **Add:** Completion tracking
- **Add:** Reward distribution (200 coins + Orange badge)
- **Add:** Redirect logic after completion

#### 4. Templates Update
- **Update:** `templates/onboarding_unified.html`
- **Add:** Progress indicators
- **Add:** Reward notifications
- **Add:** Completion celebration

#### 5. Dashboard Guards
- **Update:** `routes/coach_routes.py`
- **Add:** Onboarding check before dashboard access
- **Add:** Redirect to onboarding if incomplete

---

## 🔄 Phase 3: Membership System (After Phase 2)

### Core Requirements
- **Coach Tiers:** Free, Premium (₹299/mo), Pro (₹599/mo)
- **Employer Tiers:** Free, Premium (₹999/mo), Enterprise (custom)
- **Job Application Block:** Cannot apply without membership
- **Job Posting Block:** Cannot post jobs without membership

### Implementation Needed

#### 1. Membership Models
- **File:** `models/membership.py` (already exists)
- **Add:** Subscription validation methods
- **Add:** Feature access checking

#### 2. Membership Middleware
- **File:** `core/membership_guard.py`
- **Purpose:** Block job applications/posting without membership
- **Check:** Active subscription status

#### 3. Payment Integration
- **Update:** `routes/payment_routes.py`
- **Add:** Membership purchase flows
- **Add:** Subscription management

#### 4. Membership Templates
- **Create:** `templates/membership_plans.html`
- **Create:** `templates/subscription_status.html`
- **Update:** `templates/plans.html`

#### 5. Job Application Guards
- **Update:** `routes/coach_routes.py`
- **Add:** Membership check before job applications
- **Update:** `routes/employer_routes.py`
- **Add:** Membership check before job posting

---

## 🔄 Phase 4: Multi-City Admin Management (After Phase 3)

### Core Requirements
- **City-Based Filtering:** Admins see only their assigned cities
- **Admin Allocation:** Assign specific cities to regional admins
- **Activity Tracking:** Track admin performance by city
- **Performance Metrics:** City-wise verification statistics

### Implementation Needed

#### 1. City Filtering System
- **Update:** `routes/admin_management_routes.py`
- **Add:** City-based data filtering for regional admins
- **Add:** City assignment validation

#### 2. Verification System Integration
- **Update:** `routes/verification_routes.py`
- **Add:** City-based verification assignment
- **Add:** Admin workload distribution

#### 3. Analytics Dashboard
- **Create:** `templates/admin_city_analytics.html`
- **Add:** City-wise performance metrics
- **Add:** Admin workload visualization

#### 4. Admin Assignment Tools
- **Update:** `templates/admin_edit.html`
- **Add:** Dynamic city assignment interface
- **Add:** Workload balancing tools

---

## 🔄 Phase 5: Location Simplification (Final Phase)

### Core Requirements
- **Remove Service Radius:** No radius for academies or coaches
- **City-Based Matching:** Jobs matched by city only
- **Simplified Location:** Remove complex location logic

### Implementation Needed

#### 1. Location Model Updates
- **Update:** `models/profile.py`
- **Remove:** Service radius fields
- **Simplify:** Location to city-only

#### 2. Job Matching Logic
- **Update:** Job matching algorithms
- **Remove:** Radius-based filtering
- **Add:** City-based matching only

#### 3. Search and Filtering
- **Update:** Search functionality
- **Remove:** Distance-based searches
- **Add:** City-based filters only

#### 4. UI Updates
- **Update:** Location input forms
- **Remove:** Radius selection
- **Simplify:** City selection only

---

## 🔧 Additional Improvements Needed

### 1. ✅ Regional Admin Dashboard Enhancement - FIXED
- **Issue:** Regional admin redirects to employer registration
- **Fix:** Updated login redirect logic in `routes/auth_routes.py`
- **Status:** Both admin types now redirect to admin management dashboard

### 2. ✅ Admin Permission Testing - COMPLETE
- **Implementation:** Comprehensive test suite with 27+ test cases
- **Coverage:** Role-based access, city restrictions, permission validation
- **Files:** `tests/test_admin_permissions.py`, `test_admin_standalone.py`, `run_admin_tests.py`
- **Results:** All tests passing - admin system fully validated
- **Status:** Security, functionality, and integration thoroughly tested

### 3. Error Handling
- **Add:** Better error messages for admin operations
- **Add:** Validation for admin creation
- **Add:** Graceful failure handling

### 4. Performance Optimization
- **Add:** Database indexing for admin queries
- **Optimize:** Activity log pagination
- **Cache:** Admin permission checks

---

## 📋 Implementation Priority Order

### Immediate (Week 1)
1. **✅ Fix Regional Admin Redirect** - COMPLETE
2. **✅ Admin Permission Testing** - COMPLETE
3. **Phase 2: Onboarding Enforcement** - Next priority

### Short Term (Week 2-3)
4. **Phase 3: Membership System** - Revenue critical
5. **Error Handling Improvements** - Quality assurance

### Medium Term (Week 4-5)
6. **Phase 4: Multi-City Admin** - Scalability
7. **Performance Optimization** - User experience

### Long Term (Week 6)
8. **Phase 5: Location Simplification** - Final cleanup
9. **Additional UI/UX Improvements** - Polish

---

## 🎯 Success Criteria

### Phase 2 Complete When:
- ✅ Onboarding mandatory before profile access
- ✅ 200 coins + Orange badge awarded on completion
- ✅ Job applications blocked until onboarding complete
- ✅ Progress tracking working

### Phase 3 Complete When:
- ✅ Membership tiers implemented
- ✅ Job applications require membership
- ✅ Job posting requires membership
- ✅ Payment integration working

### Phase 4 Complete When:
- ✅ City-based admin filtering working
- ✅ Admin performance tracking by city
- ✅ Workload distribution balanced

### Phase 5 Complete When:
- ✅ Service radius removed
- ✅ City-based matching only
- ✅ Simplified location system

---

## 📝 Notes
- Each phase builds on the previous one
- Phase 1 (Admin System) is complete and working
- Focus on one phase at a time for quality
- Test thoroughly before moving to next phase
- Update this file as features are completed