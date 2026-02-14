#!/bin/bash
# Test Case Generator
# Interactive script to create structured test cases

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

echo -e "${MAGENTA}╔════════════════════════════════════════════════════════════╗${NC}"
echo -e "${MAGENTA}║           Test Case Generator                              ║${NC}"
echo -e "${MAGENTA}╚════════════════════════════════════════════════════════════╝${NC}"
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
echo -e "${YELLOW}Step 1: Basic Information${NC}"
echo -e "${MAGENTA}═══════════════════════════════════════════════════════════════${NC}"
echo ""

prompt_input "Enter Test Case ID (e.g., TC-LOGIN-001):" TC_ID true
prompt_input "Enter Test Case Title:" TC_TITLE true

prompt_select "Select Priority:" PRIORITY "P0 (Critical)" "P1 (High)" "P2 (Medium)" "P3 (Low)"

prompt_select "Select Test Type:" TEST_TYPE "Functional" "UI/Visual" "Integration" "Regression" "Performance" "Security"

prompt_input "Estimated duration (e.g., 5 minutes):" DURATION false

echo ""
echo -e "${MAGENTA}═══════════════════════════════════════════════════════════════${NC}"
echo -e "${YELLOW}Step 2: Objective${NC}"
echo -e "${MAGENTA}═══════════════════════════════════════════════════════════════${NC}"
echo ""

prompt_input "What is being tested and why? (Test objective):" OBJECTIVE true

echo ""
echo -e "${MAGENTA}═══════════════════════════════════════════════════════════════${NC}"
echo -e "${YELLOW}Step 3: Preconditions${NC}"
echo -e "${MAGENTA}═══════════════════════════════════════════════════════════════${NC}"
echo ""

echo -e "${BLUE}Enter preconditions (one per line, empty line to finish):${NC}"
PRECONDITIONS=""
while true; do
    echo -n "- "
    read -r precond
    if [ -z "$precond" ]; then
        break
    fi
    PRECONDITIONS="${PRECONDITIONS}- [ ] ${precond}\n"
done

echo ""
echo -e "${MAGENTA}═══════════════════════════════════════════════════════════════${NC}"
echo -e "${YELLOW}Step 4: Test Steps${NC}"
echo -e "${MAGENTA}═══════════════════════════════════════════════════════════════${NC}"
echo ""

echo -e "${BLUE}Enter test steps. For each step, provide:${NC}"
echo -e "${CYAN}  - Action: What to do${NC}"
echo -e "${CYAN}  - Expected: What should happen${NC}"
echo ""

STEPS=""
step_num=1
while true; do
    echo -e "${YELLOW}Step ${step_num}:${NC}"
    echo -n "  Action (empty to finish): "
    read -r action
    if [ -z "$action" ]; then
        break
    fi
    echo -n "  Expected result: "
    read -r expected

    STEPS="${STEPS}${step_num}. **${action}**\n   **Expected:** ${expected}\n\n"
    ((step_num++))
done

echo ""
echo -e "${MAGENTA}═══════════════════════════════════════════════════════════════${NC}"
echo -e "${YELLOW}Step 5: Test Data${NC}"
echo -e "${MAGENTA}═══════════════════════════════════════════════════════════════${NC}"
echo ""

prompt_input "Test data requirements (credentials, inputs, etc.):" TEST_DATA false

echo ""
echo -e "${MAGENTA}═══════════════════════════════════════════════════════════════${NC}"
echo -e "${YELLOW}Step 6: Figma Design (for UI tests)${NC}"
echo -e "${MAGENTA}═══════════════════════════════════════════════════════════════${NC}"
echo ""

FIGMA_SECTION=""
if [[ "$TEST_TYPE" == "UI/Visual" ]]; then
    prompt_input "Figma design URL:" FIGMA_URL false
    if [ -n "$FIGMA_URL" ]; then
        echo -e "${BLUE}Enter visual specifications to validate (empty line to finish):${NC}"
        VISUAL_SPECS=""
        while true; do
            echo -n "- "
            read -r spec
            if [ -z "$spec" ]; then
                break
            fi
            VISUAL_SPECS="${VISUAL_SPECS}- [ ] ${spec}\n"
        done

        FIGMA_SECTION="---

### Visual Validation

**Figma Design:** ${FIGMA_URL}

**Specifications to Validate:**
$(echo -e "$VISUAL_SPECS")
"
    fi
else
    echo -e "${CYAN}Skipping (not a UI/Visual test)${NC}"
fi

echo ""
echo -e "${MAGENTA}═══════════════════════════════════════════════════════════════${NC}"
echo -e "${YELLOW}Step 7: Additional Information${NC}"
echo -e "${MAGENTA}═══════════════════════════════════════════════════════════════${NC}"
echo ""

echo -e "${BLUE}Enter edge cases to consider (empty line to finish):${NC}"
EDGE_CASES=""
while true; do
    echo -n "- "
    read -r edge
    if [ -z "$edge" ]; then
        break
    fi
    EDGE_CASES="${EDGE_CASES}- ${edge}\n"
done

prompt_input "Related test case IDs (comma-separated):" RELATED_TCS false
prompt_input "Additional notes:" NOTES false

# Generate safe filename
SAFE_ID=$(echo "$TC_ID" | tr '[:upper:]' '[:lower:]' | tr ' ' '-' | tr -cd '[:alnum:]-')
FILENAME="${OUTPUT_DIR}/${SAFE_ID}.md"

# Generate the test case
cat > "$FILENAME" << EOF
## ${TC_ID}: ${TC_TITLE}

**Priority:** ${PRIORITY}
**Type:** ${TEST_TYPE}
**Status:** Not Run
**Estimated Time:** ${DURATION:-Not specified}
**Created:** $(date +%Y-%m-%d)
**Last Updated:** $(date +%Y-%m-%d)

---

### Objective

${OBJECTIVE}

---

### Preconditions

$(echo -e "$PRECONDITIONS")

---

### Test Steps

$(echo -e "$STEPS")

---

### Test Data

${TEST_DATA:-No specific test data required}

${FIGMA_SECTION}
---

### Post-conditions

- [ ] System state verified
- [ ] Test data cleaned up (if applicable)

---

### Edge Cases & Variations

$(if [ -n "$EDGE_CASES" ]; then echo -e "$EDGE_CASES"; else echo "None specified"; fi)

---

### Related Test Cases

${RELATED_TCS:-None}

---

### Execution History

| Date | Tester | Build | Result | Bug ID | Notes |
|------|--------|-------|--------|--------|-------|
| | | | | | |

---

### Notes

${NOTES:-None}

---

### Attachments

- [ ] Screenshots
- [ ] Test data files
- [ ] Logs

EOF

echo ""
echo -e "${GREEN}╔════════════════════════════════════════════════════════════╗${NC}"
echo -e "${GREEN}║           Test Case Created Successfully!                  ║${NC}"
echo -e "${GREEN}╚════════════════════════════════════════════════════════════╝${NC}"
echo ""
echo -e "${CYAN}Test Case ID:${NC} ${TC_ID}"
echo -e "${CYAN}File:${NC} ${FILENAME}"
echo ""
echo -e "${YELLOW}Next Steps:${NC}"
echo "  1. Review and refine test steps"
echo "  2. Add to test management system"
echo "  3. Link to requirements"
echo "  4. Schedule for execution"
echo ""

# Ask if user wants to create another
echo -e "${BLUE}Create another test case? (y/n)${NC}"
read -r another
if [[ "$another" =~ ^[Yy] ]]; then
    exec "$0" "$OUTPUT_DIR"
fi
