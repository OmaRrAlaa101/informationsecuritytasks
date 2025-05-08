#!/bin/bash

# ==============================================
# LOG FILE ANALYZER - BASH SCRIPT
# ==============================================

# Check if log file is provided
if [ $# -eq 0 ]; then
    echo "❌ Error: Please provide a log file."
    echo "Usage: $0 <log_file>"
    exit 1
fi

LOG_FILE="$1"
OUTPUT_FILE="log_analysis_report.txt"

# Check if file exists
if [ ! -f "$LOG_FILE" ]; then
    echo "❌ Error: File '$LOG_FILE' not found!"
    exit 1
fi

# Clear previous output file
> "$OUTPUT_FILE"

# Function to print section headers
section_header() {
    echo -e "\n===== $1 =====" | tee -a "$OUTPUT_FILE"
}

# 1. Total Requests
section_header "1. REQUEST COUNTS"
total_requests=$(wc -l < "$LOG_FILE")
get_requests=$(grep -c 'GET' "$LOG_FILE")
post_requests=$(grep -c 'POST' "$LOG_FILE")

echo "✅ Total requests: $total_requests" | tee -a "$OUTPUT_FILE"
echo "✅ GET requests: $get_requests" | tee -a "$OUTPUT_FILE"
echo "✅ POST requests: $post_requests" | tee -a "$OUTPUT_FILE"

# 2. Unique IPs
section_header "2. UNIQUE IP ADDRESSES"
unique_ips=$(awk '{print $1}' "$LOG_FILE" | sort | uniq | wc -l)
echo "✅ Unique IPs: $unique_ips" | tee -a "$OUTPUT_FILE"

# 3. Requests per IP & Method
section_header "3. REQUESTS PER IP (GET/POST)"
awk '{print $1, $6}' "$LOG_FILE" | sort | uniq -c | sort -nr | \
awk '{print "🔹 " $2 " made " $1 " " $3 " requests"}' | tee -a "$OUTPUT_FILE"

# 4. Failed Requests (4xx/5xx)
section_header "4. FAILED REQUESTS (4xx/5xx)"
failed_requests=$(awk '$9 ~ /^[45][0-9][0-9]$/ {count++} END {print count}' "$LOG_FILE")
failure_percent=$(awk -v total="$total_requests" -v failed="$failed_requests" \
'BEGIN {printf "%.2f%%", (failed/total)*100}')

echo "❌ Failed requests: $failed_requests" | tee -a "$OUTPUT_FILE"
echo "❌ Failure rate: $failure_percent" | tee -a "$OUTPUT_FILE"

# 5. Top User (Most Requests)
section_header "5. TOP USER (MOST ACTIVE IP)"
top_ip=$(awk '{print $1}' "$LOG_FILE" | sort | uniq -c | sort -nr | head -1)
echo "🔝 Most active IP: $top_ip" | tee -a "$OUTPUT_FILE"

# 6. Daily Request Averages
section_header "6. DAILY REQUEST AVERAGES"
dates=$(awk -F'[:[]' '{print $2}' "$LOG_FILE" | awk '{print $1}' | sort | uniq)
total_days=$(echo "$dates" | wc -l)
avg_requests=$(awk -v total="$total_requests" -v days="$total_days" \
'BEGIN {printf "%.2f", total/days}')

echo "📅 Total days logged: $total_days" | tee -a "$OUTPUT_FILE"
echo "📊 Average requests/day: $avg_requests" | tee -a "$OUTPUT_FILE"

# 7. Failure Analysis by Day
section_header "7. DAYS WITH MOST FAILURES"
awk '$9 ~ /^[45][0-9][0-9]$/ {print $4}' "$LOG_FILE" | \
awk -F'[:[]' '{print $2}' | awk '{print $1}' | sort | uniq -c | sort -nr | \
tee -a "$OUTPUT_FILE"

# 8. Requests by Hour
section_header "8. REQUESTS BY HOUR"
awk -F'[:[]' '{print $2}' "$LOG_FILE" | awk '{print $2}' | \
awk -F: '{print $1}' | sort | uniq -c | tee -a "$OUTPUT_FILE"

# 9. Status Code Breakdown
section_header "9. STATUS CODE ANALYSIS"
awk '{print $9}' "$LOG_FILE" | sort | uniq -c | sort -nr | \
tee -a "$OUTPUT_FILE"

# 10. Most Active User by Method (GET/POST)
section_header "10. MOST ACTIVE USER BY METHOD"
echo "🔸 Most GET requests:" | tee -a "$OUTPUT_FILE"
awk '$6 == "\"GET" {print $1}' "$LOG_FILE" | sort | uniq -c | sort -nr | head -1 | tee -a "$OUTPUT_FILE"
echo "🔸 Most POST requests:" | tee -a "$OUTPUT_FILE"
awk '$6 == "\"POST" {print $1}' "$LOG_FILE" | sort | uniq -c | sort -nr | head -1 | tee -a "$OUTPUT_FILE"

# 11. Failure Patterns by Hour
section_header "11. FAILURE PATTERNS BY HOUR"
awk '$9 ~ /^[45][0-9][0-9]$/ {print $4}' "$LOG_FILE" | \
awk -F: '{print $2}' | sort | uniq -c | sort -nr | \
tee -a "$OUTPUT_FILE"

# 12. Generate Suggestions
section_header "12. ANALYSIS SUGGESTIONS"
echo "📌 Based on the data, consider:" | tee -a "$OUTPUT_FILE"
echo "1. Investigate IPs with abnormal request rates." | tee -a "$OUTPUT_FILE"
echo "2. Optimize server performance during peak hours." | tee -a "$OUTPUT_FILE"
echo "3. Check for DDoS attacks if a single IP makes too many requests." | tee -a "$OUTPUT_FILE"
echo "4. Fix 404/500 errors by reviewing broken endpoints." | tee -a "$OUTPUT_FILE"
echo "5. Scale server resources if traffic exceeds capacity." | tee -a "$OUTPUT_FILE"

echo -e "\n✅ Analysis complete! Report saved to '$OUTPUT_FILE'."
