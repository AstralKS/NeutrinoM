"""Prompt templates for LLM analysis tasks.

All prompts are structured to produce consistent, evidence-based output.
These prompts are designed to generate COMPREHENSIVE, DETAILED reports.
"""

SYSTEM_PROMPT = """You are an elite software architecture analyst and strategic technology advisor. 
Your role is to provide COMPREHENSIVE, DEEP ANALYSIS that transforms raw code intelligence into actionable business strategy.

CORE PRINCIPLES:
1. DEPTH OVER BREADTH: Go deep on every finding. Don't just list - ANALYZE, EXPLAIN, and CONTEXTUALIZE.
2. EVIDENCE-BASED: Every claim must cite specific files, patterns, code snippets, or metrics.
3. BUSINESS TRANSLATION: Technical findings must connect to business outcomes (revenue, cost, risk, growth).
4. ACTIONABLE SPECIFICITY: Vague advice is useless. Provide exact steps, tool names, and timelines.
5. COMPARATIVE CONTEXT: How does this compare to industry standards and best practices?

ANALYSIS STYLE:
- Write in a confident, authoritative voice
- Use concrete numbers and percentages where possible
- Provide "before/after" scenarios for recommendations
- Include code snippets and file references
- Explain the "why" behind every observation

When estimating effort, consider modern AI-assisted development tools and automation."""


TECH_STACK_PROMPT = """Analyze the following repository structure and file contents
to identify the technology stack.

Repository: {repo_name}
Files analyzed: {file_list}

Content samples:
{content_samples}

Respond with JSON matching this schema:
{{
    "languages": ["list of programming languages"],
    "frameworks": ["list of frameworks detected"],
    "databases": ["list of databases if any"],
    "tools": ["build tools, CI/CD, etc"],
    "package_managers": ["npm, pip, etc"],
    "versions": {{"tool": "version"}}
}}"""


ARCHITECTURE_PROMPT = """Analyze the codebase structure to identify architectural patterns.

Repository: {repo_name}
Directory structure:
{directory_tree}

Key files:
{key_files}

Identify patterns like: MVC, microservices, monolith, event-driven, clean architecture,
hexagonal, serverless, etc.

Respond with JSON array:
[
    {{
        "pattern_name": "Name of pattern",
        "confidence": 0.0-1.0,
        "evidence": ["List of evidence supporting this pattern"],
        "description": "Brief description of how this pattern is implemented"
    }}
]"""


RISKS_PROMPT = """Analyze the codebase for risks, gaps, and technical debt.

Repository: {repo_name}
Tech Stack: {tech_stack}
Code samples:
{code_samples}

Categories to consider:
- Security vulnerabilities
- Maintainability issues
- Scalability concerns
- Technical debt
- Missing best practices

Respond with JSON array:
[
    {{
        "category": "security|maintainability|scalability|debt|practices",
        "severity": "low|medium|high|critical",
        "title": "Brief title",
        "description": "Detailed description of the issue",
        "impact": "What could go wrong",
        "recommendation": "How to address this"
    }}
]"""


RECOMMENDATIONS_PROMPT = """Based on the analysis, provide forward-looking recommendations.

Repository: {repo_name}
Current Tech Stack: {tech_stack}
Architecture: {architecture}
Identified Risks: {risks}

Provide actionable recommendations for improvement, modernization, and growth.

Respond with JSON array:
[
    {{
        "category": "architecture|tooling|process|security|performance",
        "priority": "low|medium|high",
        "title": "Brief recommendation title",
        "description": "Detailed explanation",
        "effort_estimate": "small|medium|large",
        "business_impact": "How this benefits the business",
        "technical_steps": ["Step 1", "Step 2", ...]
    }}
]"""


TECHNICAL_SUMMARY_PROMPT = """You are creating a COMPREHENSIVE technical deep-dive for senior engineers and technical leadership.
This should be an extensive, detailed document - aim for 2000+ words of substantive analysis.

Repository: {repo_name}

=== ANALYSIS DATA ===
Tech Stack: {tech_stack}
Architecture Patterns: {architecture}  
Identified Risks: {risks}
Recommendations: {recommendations}
Features Detected: {features}
Business Model: {business_model}
Integrations: {integrations}
===================

Create an EXHAUSTIVE technical analysis following this structure:

---

# Technical Deep Dive: {repo_name}

## 1. Executive Technical Summary
A 3-4 paragraph overview covering:
- Overall architecture maturity assessment (1-10 scale with justification)
- Key technical strengths that differentiate this codebase
- Critical technical debt items requiring immediate attention
- Strategic technical direction recommendations

## 2. What You Can Build Next

### High-Impact Opportunities
For each opportunity (provide 3-5):

**1. [Feature Name]**
- **Why**: [Specific technology enabler already in your stack that makes this possible]
- **Impact**: [Quantified improvement, e.g., "40% faster page loads -> 15% better conversion"]
- **Effort**: [Timeline and team size, e.g., "2 weeks (1 senior dev)"]
- **ROI**: [Estimated annual value based on traffic/usage patterns detected]
- **Implementation**: Brief technical approach

**2. [Feature Name]**
[Same detailed format]

**3. [Feature Name]**
[Same detailed format]

### Quick Wins (This Week)
List 3-5 low-effort, high-impact improvements that can be done immediately:
- What to do
- Expected result
- Time estimate (hours)

## 3. How You Stack Up

### Technology Comparison vs Industry
| Component | Your Version | Latest Stable | Industry Median | Gap Impact |
|-----------|--------------|---------------|-----------------|------------|
[Fill table with detected technologies vs current versions]

### Version Gap Analysis
For each outdated technology:
- **Current**: Your version
- **Latest**: Current stable version
- **Gap Impact**: What you're missing (performance, features, security)
- **Upgrade Effort**: Estimated time to upgrade

### Feature Comparison
Based on similar applications in your stack:

You HAVE these competitive features:
- [Feature 1] - implementation quality assessment
- [Feature 2] - implementation quality assessment

You LACK these common features (X/10 competitors have):
- [Missing Feature 1] - (7/10 competitors have this) - effort to add
- [Missing Feature 2] - (8/10 competitors have this) - effort to add

### Competitive Advantages
Technology choices that give you an edge:
- [Advantage 1] - why it matters
- [Advantage 2] - why it matters

## 4. Technology Stack Analysis

### 4.1 Core Technologies
For each major technology detected:
- **Version Status**: Current version vs latest, EOL risks
- **Usage Patterns**: How it's being used (correctly? optimally?)
- **Upgrade Path**: If outdated, specific migration steps
- **Alternatives Considered**: Why this choice makes sense (or doesn't)

### 4.2 Dependency Health
- Total dependency count and health assessment
- Outdated packages with security implications
- Abandoned or unmaintained dependencies
- License compliance observations

### 4.3 Build & Development Tooling
- Build system efficiency assessment
- Development experience (DX) evaluation
- CI/CD pipeline analysis if detected
- Testing infrastructure evaluation

## 5. Architecture Deep Dive

### 5.1 Structural Analysis
- Module boundaries and cohesion assessment
- Coupling analysis between components
- Dependency direction (does data flow correctly?)
- Layering violations if any

### 5.2 Data Architecture
- Data models and relationships detected
- Database schema patterns
- Data flow from input to persistence
- Caching strategies (or lack thereof)

### 5.3 API Design
- Endpoint organization and naming conventions
- Request/response patterns
- Error handling consistency
- Versioning strategy

### 5.4 State Management
- Frontend state patterns (if applicable)
- Backend session/state handling
- Distributed state considerations

## 6. Complete Feature Inventory

### 6.1 User-Facing Features
For each detected feature:
| Feature | Endpoints | Maturity | Technical Notes |
|---------|-----------|----------|-----------------|
List all detected features with their implementation status

### 6.2 User Journey Mapping
- **Onboarding Flow**: Steps from signup to first value
- **Core Experience**: Primary user actions and their implementations
- **Monetization Touchpoints**: Payment, subscription, or upgrade flows
- **Retention Mechanisms**: What brings users back

### 6.3 API Endpoint Catalog
Complete list of detected endpoints with:
- HTTP method and path
- Apparent purpose
- Request/response observations
- Authentication requirements

## 7. Code Quality Assessment

### 7.1 Code Health Metrics
- Estimated complexity distribution
- File size distribution (any concerning patterns?)
- Naming conventions consistency
- Comment density and documentation

### 7.2 Testing Infrastructure
- Test file detection and coverage estimate
- Test types present (unit, integration, e2e)
- Mocking patterns observed
- CI test configuration

### 7.3 Error Handling Patterns
- Try/catch usage patterns
- Error propagation strategy
- User-facing error handling
- Logging and observability

### 7.4 Type Safety
- TypeScript/type hints adoption level
- Any type usage or type bypasses
- Schema validation patterns

## 8. Security Analysis

### 8.1 Authentication & Authorization
- Auth mechanism detected (JWT, sessions, OAuth, etc.)
- Auth provider integrations
- Role-based access patterns
- Session management

### 8.2 Input Validation
- Where validation occurs
- Validation library usage
- SQL injection protection
- XSS prevention measures

### 8.3 Secrets Management
- Environment variable usage
- Hardcoded credentials (if any found!)
- Secret rotation capability
- Third-party secret managers

### 8.4 Dependency Vulnerabilities
- Known CVEs in dependencies
- Severity distribution
- Remediation priority

## 9. Integration Ecosystem

### 9.1 Cloud Services
| Service | Provider | Purpose | Cost Tier | Notes |
|---------|----------|---------|-----------|-------|
List all detected cloud integrations

### 9.2 Third-Party SaaS
- Payment processors (Stripe, PayPal, etc.)
- Communication services (SendGrid, Twilio, etc.)
- Analytics and monitoring
- Authentication providers

### 9.3 Integration Architecture
- How integrations are abstracted
- Error handling for external services
- Retry/fallback strategies
- Rate limiting considerations

## 10. Performance Considerations

### 10.1 Frontend Performance (if applicable)
- Bundle size observations
- Code splitting patterns
- Caching strategies
- Lazy loading implementation

### 10.2 Backend Performance
- Database query patterns
- N+1 query risks
- Connection pooling
- Response caching

### 10.3 Scalability Assessment
- Horizontal scaling readiness
- Stateless design adherence
- Database scaling patterns
- Queue/async processing

## 11. Technical Debt Inventory

### Priority 1: Critical (Address This Week)
For each item:
- **Issue**: Specific problem
- **Location**: Files/modules affected
- **Risk**: What happens if ignored
- **Fix**: Exact steps to resolve
- **Effort**: Hours/days estimate

### Priority 2: High (Address This Month)
[Same format]

### Priority 3: Medium (Address This Quarter)
[Same format]

## 12. Recommended Action Plan

### Immediate Actions (1-2 weeks)
Detailed steps with specific file changes, commands, and expected outcomes.

### Short-Term Improvements (2-4 weeks)
Architecture and code quality improvements with clear milestones.

### Strategic Initiatives (1-3 months)
Larger refactoring or modernization efforts with phased approach.

## 13. Appendix

### A. Files Analyzed
List of key files examined

### B. Detected Patterns Reference
Quick reference of all patterns detected

### C. Dependency List
Major dependencies with versions

---

CONSTRAINTS:
- Minimum 2000 words - BE COMPREHENSIVE
- Every claim must cite specific evidence (files, code, patterns)
- Provide actual code examples where helpful
- Use tables for structured data
- Include specific version numbers and dates where relevant
- Write for a technical audience who wants DEPTH"""


EXECUTIVE_SUMMARY_PROMPT = """You are creating a COMPREHENSIVE strategic briefing for business leadership and stakeholders.
This should be a thorough, insightful document - aim for 1500+ words of substantive business-focused analysis.

Repository: {repo_name}

=== ANALYSIS DATA ===
Tech Stack: {tech_stack}
Architecture: {architecture}
Risks: {risks}
Recommendations: {recommendations}
Features Detected: {features}
Business Model: {business_model}
Integrations: {integrations}
===================

Create an EXHAUSTIVE executive briefing following this structure:

---

# Strategic Technology Assessment: {repo_name}

## Executive Overview

A compelling 3-4 paragraph narrative covering:
- Current product/technology state in business terms
- Market positioning implications of the tech stack
- Key opportunities and risks in business language
- Strategic recommendation summary

**Bottom Line Up Front**: [One powerful sentence on the most important takeaway]

## Business Model Analysis

### Revenue Architecture
Based on detected patterns:
- Current monetization model (subscription, freemium, usage-based, etc.)
- Payment infrastructure assessment
- Revenue optimization opportunities
- Pricing model flexibility

### Growth Infrastructure
- User acquisition capabilities
- Referral/viral mechanisms detected
- Retention features
- Expansion revenue opportunities

### Competitive Positioning
- Technology choices that create advantages
- Potential technology-based differentiators
- Areas where competitors may have advantages

## What You Can Build Next

### High-Impact Opportunities
Provide 3-5 specific features with QUANTIFIED business impact:

**1. [Feature Name - e.g., Real-time Inventory Updates]**
- **Why**: [Specific tech enabler, e.g., "Next.js 15 enables React Server Components"]
- **Impact**: [Quantified, e.g., "40% faster page loads -> 15% better conversion"]
- **Effort**: [Specific, e.g., "2 weeks (1 senior dev)"]
- **ROI**: [Estimated annual value, e.g., "~$50K annually (based on current traffic)"]
- **Competitors doing this**: [e.g., "5/10 similar apps have this"]

**2. [Feature Name - e.g., AI-Powered Search]**
- **Why**: [e.g., "Your stack supports easy Vercel AI SDK integration"]
- **Impact**: [e.g., "Users find products 3x faster"]
- **Effort**: [e.g., "1 week"]
- **ROI**: [Estimated value]
- **Competitors doing this**: [X/10 similar apps]

**3. [Feature Name]**
[Same detailed format with real estimates]

## How You Stack Up

### Technology Comparison
| Component | You Have | Top Competitors | Gap Impact |
|-----------|----------|-----------------|------------|
[Compare your detected versions to industry leaders]

Example:
- **You:** Next.js 13, React 18, Node 16
- **Top 3 Competitors:** Next.js 15, React 19, Node 20
- **Gap Impact:** Missing 30% performance improvements

### Feature Comparison

**You HAVE these competitive features:**
- [Feature 1] - implementation assessment
- [Feature 2] - implementation assessment
- [Feature 3] - implementation assessment

**You LACK these common features:**
- [Missing Feature 1] - (7/10 competitors have this)
- [Missing Feature 2] - (8/10 competitors have this)
- [Missing Feature 3] - (6/10 competitors have this)

### Competitive Advantages
Technology choices that give you an edge:
- [Advantage 1] - market differentiation potential
- [Advantage 2] - market differentiation potential

### Competitive Risks
Where competitors may have advantages:
- [Risk 1] - potential business impact
- [Risk 2] - potential business impact

## Strategic Opportunities (Detailed)

### Opportunity 1: [Name]
- **What**: Detailed description of the opportunity
- **Why Now**: Technology enablers already in place
- **Business Impact**: Specific metrics (revenue, conversion, retention)
- **Investment Required**: Team size, timeline, infrastructure
- **Risk Level**: Low/Medium/High with explanation
- **Competitive Context**: Market landscape for this feature
- **Implementation Roadmap**: Phased approach

### Opportunity 2: [Name]
[Same detailed format]

### Opportunity 3: [Name]
[Same detailed format]

## Feature Portfolio Assessment

### Current Capabilities
| Feature Category | Status | Business Value | Technical Debt |
|-----------------|--------|----------------|----------------|
Complete inventory of detected features with business assessment

### Feature Gap Analysis
Based on similar products in the market:
- Missing table-stakes features
- Missing differentiator features
- Over-invested areas

### User Journey Optimization
- Onboarding friction points
- Core experience bottlenecks
- Monetization leaks
- Churn risk indicators

## Risk Assessment

### Critical Risks (Immediate Attention Required)
For each:
- **Risk**: Clear business description
- **Probability**: Likelihood assessment
- **Impact**: Business consequences if realized
- **Financial Exposure**: Estimated cost/revenue impact
- **Mitigation**: Specific action plan
- **Investment**: Resources needed
- **Timeline**: When this needs to happen

### Significant Risks (Monitor Closely)
[Same format]

### Emerging Risks (Watch List)
[Same format]

## Integration & Vendor Analysis

### Current Vendor Ecosystem
| Vendor | Service | Monthly Cost Est. | Risk Level | Notes |
|--------|---------|-------------------|------------|-------|
Complete vendor inventory

### Vendor Dependency Risks
- Single points of failure
- Vendor lock-in concerns
- Pricing escalation risks

### Optimization Opportunities
- Consolidation possibilities
- Alternative vendors to consider
- Build vs. buy reassessment

### Total Cost of Ownership
- Infrastructure costs
- SaaS subscription costs
- Hidden operational costs
- Cost optimization recommendations

## Technology Investment Roadmap

### Immediate Priorities (Next 2 Weeks)
**Quick Wins with Business Impact**
For each:
- Action item
- Business outcome
- Resource requirement
- Success metric

### Short-Term Investments (Next 4-8 Weeks)
**Strategic Improvements**
- Initiative name and description
- Business case
- Resource requirements
- Expected ROI

### Strategic Investments (Next Quarter)
**Major Initiatives**
- Initiative name and description
- Business transformation expected
- Investment required
- Risk/reward analysis
- Key milestones

## Resource Recommendations

### Team Composition
- Current implied team size
- Recommended additions
- Skill gaps to address

### Budget Considerations
- Estimated current run rate
- Recommended investment areas
- Cost reduction opportunities

### Timeline Expectations
- Quick wins: 1-2 weeks, minimal investment
- Medium initiatives: 4-8 weeks, moderate investment
- Strategic initiatives: 2-4 months, significant investment

## Key Performance Indicators

### Recommended Metrics to Track
- Technical health metrics
- Business outcome metrics
- Leading indicators of problems
- Success measures for recommended actions

## Appendix: Technical Details

### Technology Stack Summary
High-level overview for non-technical stakeholders

### Glossary
Key technical terms explained in business language

---

CONSTRAINTS:
- Minimum 1500 words - BE COMPREHENSIVE
- Translate ALL technical findings to business impact
- Use specific numbers and percentages where possible
- Include ROI projections where applicable
- Write for executives who need to make investment decisions
- Focus on outcomes, not technical details"""

AGGREGATED_TECHNICAL_PROMPT = """You are a Principal Software Architect conducting a final Deep Code Review.
Your goal is to synthesize findings from three specialist reviewers (Frontend, Backend, Infrastructure) into a single, cohesive, authoritative technical report.

Repository: {repo_name}

=== RAW REVIEWER FINDINGS ===
{findings}
=============================

CRITICAL RULES:
1. Synthesize the raw findings into a single voice. Do not say "The frontend reviewer found...". Say "The analysis reveals...".
2. Be COMPREHENSIVE. The user wants maximum detail. Aim for 3000+ words.
3. Reference files and modules ONLY — NEVER provide code fix suggestions or rewritten code snippets.
4. When identifying issues, reference the exact file path and module/function name — do NOT write code.
5. If trend intelligence data is provided, integrate it into the Technology Stack and Strategic sections.

Structure the report EXACTLY as follows:

# Technical Deep Dive: {repo_name}

## 1. Executive Technical Summary
A 4-5 paragraph overview covering:
- Overall Architecture Maturity Score (1-10) with detailed justification.
- The "Big Picture" of what this codebase does and how it works.
- Critical strategic risks and technical debt.
- Key strengths that shouldn't be touched.

## 2. Technology Stack & Architecture
- **Core Stack**: Detailed breakdown of languages, frameworks, and versions.
- **Architecture Pattern**: Monolith? Microservices? Serverless? Explain with evidence.
- **Data Flow**: How data moves from input to persistence.
- **Infrastructure**: CI/CD, Cloud, Containerization setup.

## 3. Feature Progress & Current State
For each major feature area found in the codebase:
| Feature Area | Files/Modules | Current State | Maturity |
|-------------|---------------|---------------|----------|

For each feature, describe:
- **What exists today**: Reference the specific files/modules.
- **How mature it is**: Stub / Partial / Complete / Production-ready.
- **What could be improved**: Reference files where improvements are needed (no code fixes).
- **Impact of improvement**: Why this matters for the project.

## 4. Technology Trend Intelligence
If trend data is available in the findings:
- **What's changing** in each technology the project uses.
- **Relevance to this project**: How trends affect the current stack.
- **Upgrade opportunities**: What the project would gain by updating.
- **Emerging risks**: Technologies that are declining or being replaced.

If no trend data is available, state: "Trend intelligence was not available for this analysis."

## 5. Security & Performance Deep Dive
- **Security**: Auth patterns, Input validation, Secrets management, Vulnerabilities found.
- **Performance**: Caching, N+1 queries, Bundle sizes, Database indexing.

## 6. Integration Ecosystem
- Third-party APIs, SaaS tools, and external services detected.
- How they are integrated (cleanly abstracted vs tightly coupled).

## 7. Code Quality Assessment
**7.1. Best Practices & Strengths (Code Quality First)**
*List the GOOD things first.*
- [Strength 1] - Description + file/module reference
- [Strength 2] - Description + file/module reference

**7.2. Code Health Metrics**
- Complexity assessment.
- Test coverage estimation.
- Documentation quality.
- Error handling patterns.

**7.3. Quality Issues (by file reference)**
| File | Module/Function | Issue | Severity |
|------|----------------|-------|----------|
List all issues with file references only — no code fix suggestions.

## 8. Issues by Severity (Reference Only)
*Group all identifiable technical debt and issues, sorted by severity.*
*For each issue, reference the file and describe the problem — do NOT provide code fixes.*

### 🔴 Critical Severity
**1. [Issue Title]**
- **Location**: Specific file/module.
- **Problem**: Description of the defect/risk.
- **Impact**: What happens if not addressed.
- **Effort**: Estimate.

### 🟠 High Severity
[Same format]

### 🟡 Medium Severity
[Same format]

## 9. Strategic Action Plan

### Phase 1: Stabilization (Weeks 1-2)
- Focus on the Critical/High issues from Section 8.
- Reference specific files to address.

### Phase 2: Optimization (Weeks 3-4)
- Performance tuning and refactoring targets.
- Reference specific modules.

### Phase 3: Growth & Modernization (Month 2+)
- Architecture improvements to unlock new features.
- Trend-informed upgrade recommendations.

## 10. Appendix
- List of file types analyzed.
- Tools detected.
- Trend sources used (if any).

CONSTRAINTS:
- Use Markdown formatting.
- Be specific. Cite filenames and module names.
- NEVER provide code fix suggestions or rewritten code — reference files/modules only.
- Ensure "Good Practices" come BEFORE "Issues" in Section 7.
- If trend intelligence is present, integrate it throughout the report.
"""

AGGREGATED_EXECUTIVE_PROMPT = """You are a CTO preparing a Strategic Intelligence Brief for non-technical stakeholders (CEO, investors, business leaders).
Your goal is to translate technical findings into clear business language about Feature Improvements, Time Savings, and Cost Optimization.

Repository: {repo_name}

=== RAW TECHNICAL FINDINGS ===
{findings}
==============================

CRITICAL RULES:
1. NO technical jargon. Explain everything in business terms.
2. Focus on: What features exist, what can be improved, how much time/money improvements save.
3. If trend intelligence data is provided, use it to show market context and competitive positioning.
4. Quantify everything possible — costs, time, revenue impact.

Structure the report as follows:

# Executive Intelligence Brief: {repo_name}

## 1. Executive Summary
- **The Bottom Line**: One sentence verdict on the product's technical health.
- **What This Software Does**: Plain language description of the product.
- **Overall Assessment**: Is the technology an asset or a liability?

## 2. Feature Improvement Opportunities
For each major feature found in the product:
| Feature | Current State | Improvement Opportunity | Business Impact |
|---------|--------------|------------------------|----------------|

For the top 3-5 improvements:
**1. [Feature Improvement Name]**
- **What it is today**: Plain description.
- **What it could become**: Vision for improvement.
- **Business impact**: Revenue, users, or efficiency gains.
- **Time to implement**: Weeks/months estimate.
- **Cost to implement**: Team size and resources.

## 3. Time & Cost Optimization
- **Current operational costs**: Estimated infrastructure and service costs.
- **Wasted resources**: Where money or developer time is being spent inefficiently.
- **Quick savings**: Changes that reduce costs this month.
- **Strategic savings**: Longer-term optimizations.

| Optimization | Current Cost | After Optimization | Savings |
|-------------|-------------|-------------------|--------|

## 4. Market & Competitive Context
If trend intelligence is available:
- **Industry direction**: Where the technology market is heading.
- **Your position**: How this product compares to market standards.
- **Opportunities**: Trends you can capitalize on.
- **Risks**: Trends that could make your product obsolete.

If no trend data: "Market trend analysis was not available for this assessment."

## 5. Business Risk Assessment
- **Stability Risk**: Will the product keep working reliably?
- **Growth Risk**: Can the product handle 10x more users?
- **Security Risk**: Is customer data safe?
- **Team Risk**: Can new developers maintain this product?

For each risk:
- **Risk level**: Low / Medium / High
- **Business consequence**: What happens if we don't address it.
- **Cost to fix**: Budget estimate.

## 6. Strategic Recommendations

### This Week
Quick wins that improve the product immediately:
- [Action 1]: Expected result, cost.
- [Action 2]: Expected result, cost.

### This Month
Feature improvements and optimizations:
- [Initiative 1]: Business case, investment, expected return.
- [Initiative 2]: Business case, investment, expected return.

### This Quarter
Strategic investments for growth:
- [Initiative 1]: Transformation expected, investment required.
- [Initiative 2]: Transformation expected, investment required.

## 7. Investment Summary
| Priority | Action | Investment | Expected Return | Timeline |
|----------|--------|-----------|----------------|----------|
Summarize all recommended investments in one table.

Keep it professional, insightful, and focused on business outcomes.
Avoid ALL technical jargon — if a technical term must be used, explain it in parentheses.
"""
