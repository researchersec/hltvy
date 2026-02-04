# CS:GO/CS2 Betting Data Collection

🤖 **Automated data collection system for CS:GO/CS2 match odds and results**

## 📊 Current Statistics

**Last Updated:** 2026-02-04 23:27:08 UTC

### Upcoming Matches
- **Total matches with odds:** 0/0
- **Active bookmakers:** None
- **Most frequent teams:** None

### Historical Results  
- **Total matches collected:** 2,120
- **Enriched with details:** 2,120 (100.0%)
- **Date range:** 1770228900000 to 1770232200000
- **Top events:** Digital Crusade DraculaN Season 4, Digital Crusade DraculaN Season 3, CCT Season 3 South America Series 7
- **Most played maps:** Ancient, Mirage, Dust2

## 🔄 Automation

This repository automatically collects data every 4 hours using GitHub Actions:
- **Odds collection** from HLTV betting section
- **Results scraping** with detailed match statistics  
- **Data validation** and error handling
- **Automatic commits** when new data is available

## 📁 Data Files

- `upcoming.json` - Current matches with betting odds
- `results.json` - Historical match results with detailed statistics
- `scrape_state.json` - Scraping progress state (auto-generated)
- `failed_urls.json` - Failed URL log for debugging (auto-generated)

## 🛠️ Technical Details

**Dependencies:**
- Python 3.11+
- FlareSolverr (Docker container for Cloudflare bypass)
- BeautifulSoup4 for HTML parsing
- Requests for HTTP handling

**Data Sources:**
- HLTV.org betting odds
- HLTV.org match results and statistics

---
*This README is automatically updated by the data collection system.*
