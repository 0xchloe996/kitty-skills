#!/bin/bash
# Bug Report Generator
# Interactive script to create structured bug reports

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
MAGENTA='\033[0;35m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

# Output directory (optional argument)
OUTPUT_DIR="${1:-.}"

# Generate unique bug ID
BUG_ID="BUG-$(date +%Y%m%d%H%M%S)"

echo -e "${MAGENTA}╔════════════════════════════════════════════════════════════╗${NC}"
echo -e "${MAGENTA}║           Bug Report Generator                             ║${NC}"
echo -e "${MAGENTA}╚════════════════════════════════════════════════════════════╝${NC}"
echo ""
echo -e "${CYAN}Bug ID: ${BUG_ID}${NC}"
echo ""

# Function to prompt for input
prompt_input() {
    local prompt="$1"
    local var_name="$2"
    local required="${3:-false}"
    local value=""

    while true; do
        echo -e "${BLUE}${prompt}${NC}"
        read -r value
        if [ "$required" = "true" ] && [ -z "$value" ]; then
            echo -e "${RED}This field is required. Please enter a value.${NC}"
        else
            eval "$var_name=\"\$value\""
            break
        fi
    done
}

# Function to prompt for selection
prompt_select() {
    local prompt="$1"
    local var_name="$2"
    shift 2
    local options=("$@")

    echo -e "${BLUE}${prompt}${NC}"
    for i in "${!options[@]}"; do
        echo "  $((i+1)). ${options[$i]}"
    done

    while true; do
        read -r selection
        if [[ "$selection" =~ ^[0-9]+$ ]] && [ "$selection" -ge 1 ] && [ "$selection" -le "${#options[@]}" ]; then
            eval "$var_name=\"\${options[$((selection-1))]}\""
            break
        else
            echo -e "${RED}Invalid selection. Please enter a number between 1 and ${#options[@]}.${NC}"
        fi
    done
}

echo -e "${MAGENTA}═══════════════════════════════════════════════════════════════${NC}"
echo -e "${YELLOW}Section 1: Basic Information${NC}"
echo -e "${MAGENTA}═══════════════════════════════════════════════════════════════${NC}"
echo ""

prompt_input "Enter bug title (be specific, e.g., '[Login] Password reset email not sent'):" BUG_TITLE true

prompt_select "Select severity:" SEVERITY "Critical" "High" "Medium" "Low"

prompt_select "Select priority:" PRIORITY "P0 (Immediate)" "P1 (High)" "P2 (Medium)" "P3 (Low)"

prompt_select "Select bug type:" BUG_TYPE "Functional" "UI/Visual" "Performance" "Security" "Data" "Crash"

echo ""
echo -e "${MAGENTA}═══════════════════════════════════════════════════════════════${NC}"
echo -e "${YELLOW}Section 2: Environment${NC}"
echo -e "${MAGENTA}═══════════════════════════════════════════════════════════════${NC}"
echo ""

prompt_input "Operating System (e.g., macOS 14, Windows 11, Ubuntu 22.04):" OS_INFO true
prompt_input "Browser and version (e.g., Chrome 120, Firefox 121):" BROWSER_INFO true
prompt_input "Device type (e.g., Desktop, iPhone 15, Samsung Galaxy S23):" DEVICE_INFO true
prompt_input "Build/Version number:" BUILD_VERSION true
prompt_input "URL where bug occurs:" BUG_URL false

echo ""
echo -e "${MAGENTA}═══════════════════════════════════════════════════════════════${NC}"
echo -e "${YELLOW}Section 3: Bug Details${NC}"
echo -e "${MAGENTA}═══════════════════════════════════════════════════════════════${NC}"
echo ""

prompt_input "Brief description of the bug (2-3 sentences):" DESCRIPTION true

echo ""
echo -e "${BLUE}Enter steps to reproduce (one step per line, empty line to finish):${NC}"
STEPS=""
step_num=1
while true; do
    echo -n "Step $step_num: "
    read -r step
    if [ -z "$step" ]; then
        break
    fi
    STEPS="${STEPS}${step_num}. ${step}\n"
    ((step_num++))
done

prompt_input "Expected behavior (what should happen):" EXPECTED true
prompt_input "Actual behavior (what actually happens):" ACTUAL true

prompt_select "Reproduction rate:" REPRO_RATE "Always (100%)" "Often (>50%)" "Sometimes (<50%)" "Rarely" "Once"

echo ""
echo -e "${MAGENTA}═══════════════════════════════════════════════════════════════${NC}"
echo -e "${YELLOW}Section 4: Impact Assessment${NC}"
echo -e "${MAGENTA}═══════════════════════════════════════════════════════════════${NC}"
echo ""

prompt_input "Who is affected? (e.g., All users, Admin users, New users):" AFFECTED_USERS false
prompt_input "Is there a workaround? (describe or 'None'):" WORKAROUND false
prompt_input "Business impact (e.g., Revenue loss, User frustration, Minimal):" BUSINESS_IMPACT false

echo ""
echo -e "${MAGENTA}═══════════════════════════════════════════════════════════════${NC}"
echo -e "${YELLOW}Section 5: Additional Information${NC}"
echo -e "${MAGENTA}═══════════════════════════════════════════════════════════════${NC}"
echo ""

prompt_input "Console errors (paste any errors, or 'None'):" CONSOLE_ERRORS false
prompt_input "Related feature/ticket ID (e.g., FEAT-123):" RELATED_TICKET false
prompt_input "Is this a regression? (Yes/No):" IS_REGRESSION false
prompt_input "If regression, last working version:" LAST_WORKING false
prompt_input "Additional notes:" NOTES false

# Generate the bug report
FILENAME="${OUTPUT_DIR}/${BUG_ID}.md"

cat > "$FILENAME" << EOF
# ${BUG_ID}: ${BUG_TITLE}

**Severity:** ${SEVERITY}
**Priority:** ${PRIORITY}
**Type:** ${BUG_TYPE}
**Status:** Open
**Reporter:** $(whoami)
**Reported Date:** $(date +%Y-%m-%d)

---

## Environment

| Property | Value |
|----------|-------|
| **OS** | ${OS_INFO} |
| **Browser** | ${BROWSER_INFO} |
| **Device** | ${DEVICE_INFO} |
| **Build/Version** | ${BUILD_VERSION} |
| **URL** | ${BUG_URL:-N/A} |

---

## Description

${DESCRIPTION}

---

## Steps to Reproduce

$(echo -e "$STEPS")

**Reproduction Rate:** ${REPRO_RATE}

---

## Expected Behavior

${EXPECTED}

---

## Actual Behavior

${ACTUAL}

---

## Visual Evidence

**Screenshots:**
- [ ] Before state: [attach]
- [ ] After state: [attach]
- [ ] Error message: [attach]

**Console Errors:**
\`\`\`
${CONSOLE_ERRORS:-None reported}
\`\`\`

---

## Impact Assessment

| Aspect | Details |
|--------|---------|
| **Users Affected** | ${AFFECTED_USERS:-Not specified} |
| **Workaround** | ${WORKAROUND:-None} |
| **Business Impact** | ${BUSINESS_IMPACT:-Not assessed} |

---

## Additional Context

**Related Items:**
- Ticket: ${RELATED_TICKET:-None}
- Regression: ${IS_REGRESSION:-Unknown}
- Last Working Version: ${LAST_WORKING:-N/A}

**Notes:**
${NOTES:-None}

---

## Developer Section

### Root Cause
[To be filled by developer]

### Fix Description
[To be filled by developer]

### Files Changed
- [ ] [file1]
- [ ] [file2]

### Fix PR
[Link to PR]

---

## QA Verification

- [ ] Fix verified in dev environment
- [ ] Fix verified in staging
- [ ] Regression tests passed
- [ ] Ready for production

**Verified By:**
**Verification Date:**
**Verification Build:**

---

## Discussion

[Add comments and updates here]

EOF

echo ""
echo -e "${GREEN}╔════════════════════════════════════════════════════════════╗${NC}"
echo -e "${GREEN}║           Bug Report Created Successfully!                 ║${NC}"
echo -e "${GREEN}╚════════════════════════════════════════════════════════════╝${NC}"
echo ""
echo -e "${CYAN}Bug ID:${NC} ${BUG_ID}"
echo -e "${CYAN}File:${NC} ${FILENAME}"
echo ""
echo -e "${YELLOW}Next Steps:${NC}"
echo "  1. Attach screenshots/screen recordings"
echo "  2. Add console logs if applicable"
echo "  3. Submit to bug tracking system"
echo "  4. Link to related test cases"
echo ""
