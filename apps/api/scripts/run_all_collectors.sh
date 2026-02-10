#!/usr/bin/env bash
# ---------------------------------------------------------------------------
# Run all collectors sequentially (excluding mustdo, which is deprecated).
#
# Usage:
#   cd apps/api
#   bash scripts/run_all_collectors.sh
#
# Each collector runs with --delay 2 and --future-only where supported.
# The script tracks pass/fail per collector and prints a summary at the end.
# ---------------------------------------------------------------------------

set -euo pipefail

# ── Colours (disabled when stdout isn't a terminal) ──────────────────────
if [[ -t 1 ]]; then
    RED='\033[0;31m'
    GREEN='\033[0;32m'
    YELLOW='\033[1;33m'
    CYAN='\033[0;36m'
    BOLD='\033[1m'
    RESET='\033[0m'
else
    RED='' GREEN='' YELLOW='' CYAN='' BOLD='' RESET=''
fi

# ── Source ID mapping ────────────────────────────────────────────────────
# Van Wezel Performing Arts Hall | id: 1
# Mote Marine Laboratory and Aquarium | id: 2
# ArtFestival.com | id: 3
# Asolo Repertory Theatre | id: 4
# Big Top Brewing | id: 5
# Big Waters Land Trust | id: 6
# Sarasota Fair | id: 7
# Selby Gardens | id: 8

DELAY=2

PASSED=0
FAILED=0
FAILED_NAMES=()
TOTAL=8

# ── Helper ───────────────────────────────────────────────────────────────

run_collector() {
    local name="$1"
    local module="$2"
    shift 2
    local args=("$@")

    echo ""
    echo -e "${BOLD}${CYAN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${RESET}"
    echo -e "${BOLD}  ▶ Running: ${name}${RESET}"
    echo -e "${CYAN}    python -m ${module} ${args[*]}${RESET}"
    echo -e "${BOLD}${CYAN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${RESET}"

    local start_time
    start_time=$(date +%s)

    if python -m "$module" "${args[@]}"; then
        local end_time
        end_time=$(date +%s)
        local elapsed=$(( end_time - start_time ))
        echo -e "${GREEN}  ✔ ${name} completed successfully (${elapsed}s)${RESET}"
        PASSED=$(( PASSED + 1 ))
    else
        local exit_code=$?
        local end_time
        end_time=$(date +%s)
        local elapsed=$(( end_time - start_time ))
        echo -e "${RED}  ✘ ${name} FAILED (exit code ${exit_code}, ${elapsed}s)${RESET}"
        FAILED=$(( FAILED + 1 ))
        FAILED_NAMES+=("$name")
    fi
}

# ── Run collectors ───────────────────────────────────────────────────────

echo -e "${BOLD}Starting all collectors (${TOTAL} total, delay=${DELAY}s)${RESET}"
echo -e "Time: $(date '+%Y-%m-%d %H:%M:%S')"

OVERALL_START=$(date +%s)

# 1. Van Wezel (no --future-only flag available)
run_collector "Van Wezel Performing Arts Hall" \
    app.collectors.vanwezel \
    --source-id 1 --delay "$DELAY"

# 2. Mote Marine (feed-based, has --future-only)
run_collector "Mote Marine Laboratory and Aquarium" \
    app.collectors.mote \
    --source-id 2 --delay "$DELAY" --future-only

# 3. ArtFestival.com (no --future-only flag available)
run_collector "ArtFestival.com" \
    app.collectors.artfestival \
    --source-id 3 --delay "$DELAY"

# 4. Asolo Repertory Theatre (has --future-only)
run_collector "Asolo Repertory Theatre" \
    app.collectors.asolorep \
    --source-id 4 --delay "$DELAY" --future-only

# 5. Big Top Brewing (feed-based, has --future-only)
run_collector "Big Top Brewing" \
    app.collectors.bigtop \
    --source-id 5 --delay "$DELAY" --future-only

# 6. Big Waters Land Trust (future-only is the default; --include-past omitted)
run_collector "Big Waters Land Trust" \
    app.collectors.bigwaters \
    --source-id 6 --delay "$DELAY"

# 7. Sarasota Fair (no --future-only flag available)
run_collector "Sarasota Fair" \
    app.collectors.sarasotafair \
    --source-id 7 --delay "$DELAY"

# 8. Selby Gardens (feed-based, has --future-only)
run_collector "Selby Gardens" \
    app.collectors.selby \
    --source-id 8 --delay "$DELAY" --future-only

# ── Summary ──────────────────────────────────────────────────────────────

OVERALL_END=$(date +%s)
OVERALL_ELAPSED=$(( OVERALL_END - OVERALL_START ))

echo ""
echo -e "${BOLD}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${RESET}"
echo -e "${BOLD}  SUMMARY${RESET}"
echo -e "${BOLD}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${RESET}"
echo -e "  Total time : ${OVERALL_ELAPSED}s"
echo -e "  ${GREEN}Passed     : ${PASSED}/${TOTAL}${RESET}"

if [[ $FAILED -gt 0 ]]; then
    echo -e "  ${RED}Failed     : ${FAILED}/${TOTAL}${RESET}"
    echo -e "  ${RED}Failed collectors:${RESET}"
    for name in "${FAILED_NAMES[@]}"; do
        echo -e "    ${RED}• ${name}${RESET}"
    done
    echo ""
    echo -e "${RED}${BOLD}Some collectors failed. Check the output above for details.${RESET}"
    exit 1
else
    echo ""
    echo -e "${GREEN}${BOLD}All collectors completed successfully!${RESET}"
    exit 0
fi
