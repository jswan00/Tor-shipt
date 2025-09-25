import requests
from bs4 import BeautifulSoup
import datetime
import os
import re
import csv
import configparser
import time
import json
import matplotlib.pyplot as plt
import matplotlib.dates as mdates

class SEOAnalyzer:
    """
    Ek highly advanced SEO analyzer jo website ko scan karke
    ek professional, actionable markdown report aur historical trend charts generate karta hai.
    """
    def __init__(self, config_path='config.ini'):
        print("🤖 Advanced SEO Bot Initializing...")
        self.config = configparser.ConfigParser()
        if not os.path.exists(config_path):
            raise FileNotFoundError(f"Configuration file not found at: {config_path}")
        self.config.read(config_path)

        # --- Load Configuration ---
        self.url = self.config.get('SEO', 'url')
        self.keywords = [k.strip() for k in self.config.get('SEO', 'keywords').split(',')]
        self.report_dir = self.config.get('REPORT', 'directory')
        self.report_file = os.path.join(self.report_dir, self.config.get('REPORT', 'report_file'))
        self.trend_chart = os.path.join(self.report_dir, self.config.get('REPORT', 'trend_chart'))
        self.score_chart = os.path.join(self.report_dir, "seo_score_donut.png") # New chart
        self.history_file = os.path.join(self.report_dir, self.config.get('REPORT', 'history_file'))
        
        self.results = {}
        self.total_score = 0
        self.max_score = 0
        os.makedirs(self.report_dir, exist_ok=True)
        print(f"📈 Configuration loaded for URL: {self.url}")

    def get_score_emoji(self, score, max_score):
        """Score ke basis par emoji return karta hai."""
        if max_score == 0: return "⚪"
        percentage = (score / max_score) * 100
        if percentage >= 85: return "🟢"  # Excellent
        if percentage >= 60: return "🟡"  # Good
        return "🔴"  # Needs Improvement

    def run_analysis(self):
        """Saare SEO checks ko orchestrate aur run karta hai."""
        print(f"🚀 Fetching and analyzing {self.url}...")
        try:
            start_time = time.time()
            headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'}
            response = requests.get(self.url, timeout=20, headers=headers)
            self.load_time = time.time() - start_time
            response.raise_for_status()
            self.soup = BeautifulSoup(response.text, "html.parser")
            self.text_content = self.soup.get_text(separator=' ', strip=True).lower()
            self.word_count = len(self.text_content.split())

            # Run all check categories
            self.check_core_vitals()
            self.check_content_and_keywords()
            self.check_technical_seo()
            self.check_links()
            self.check_social_and_schema()

            print("✅ Analysis complete.")
            return True
        except requests.RequestException as e:
            print(f"❌ Critical Error: Failed to fetch URL. Reason: {e}")
            return False
        except Exception as e:
            print(f"❌ An unexpected error occurred: {e}")
            return False

    # --- Individual Check Categories ---

    def check_core_vitals(self):
        """Title, Meta Description, aur Performance check karta hai."""
        # Title Tag
        title = self.soup.title.string.strip() if self.soup.title else ""
        score, advice = (10, ["✅ Length is optimal (10-60 chars)."]) if 10 < len(title) < 60 else (0, ["❌ Length should be 10-60 chars."])
        self.add_result('Core Vitals', 'Title Tag', score, 10, {'text': title, 'length': len(title)}, advice)

        # Meta Description
        meta_desc_tag = self.soup.find("meta", attrs={"name": "description"})
        desc = meta_desc_tag['content'].strip() if meta_desc_tag else ""
        score, advice = (10, ["✅ Length is optimal (70-160 chars)."]) if 70 < len(desc) < 160 else (0, ["❌ Length should be 70-160 chars."])
        self.add_result('Core Vitals', 'Meta Description', score, 10, {'text': desc, 'length': len(desc)}, advice)

        # Performance
        score, advice = (10, ["✅ Excellent load time (< 2s)."]) if self.load_time < 2 else \
                        (5, ["🟡 Good load time (< 4s), but can be improved."]) if self.load_time < 4 else \
                        (0, ["🔴 Slow load time (> 4s). Optimize resources."])
        self.add_result('Core Vitals', 'Page Load Time', score, 10, {'time': f"{self.load_time:.2f}s"}, advice)

    def check_content_and_keywords(self):
        """Headings, Keywords, Image SEO, aur Word Count check karta hai."""
        # Heading Structure
        h1s = [h.text.strip() for h in self.soup.find_all('h1')]
        h2s = [h.text.strip() for h in self.soup.find_all('h2')]
        score, advice = 0, []
        if len(h1s) == 1:
            score += 10; advice.append("✅ Exactly one H1 tag found.")
        else:
            advice.append(f"❌ Found {len(h1s)} H1 tags. There must be only one.")
        if len(h2s) > 0:
            score += 5; advice.append(f"✅ Found {len(h2s)} H2 tags for structure.")
        else:
            advice.append("🟡 No H2 tags found. Use H2s to structure content.")
        self.add_result('Content & Keywords', 'Heading Structure', score, 15, {'h1_count': len(h1s), 'h2_count': len(h2s)}, advice)

        # Keyword Analysis
        keyword_data, score = {}, 0
        title_text = self.results['Core Vitals']['Title Tag']['data']['text'].lower()
        meta_text = self.results['Core Vitals']['Meta Description']['data']['text'].lower()
        for kw in self.keywords:
            kw_lower = kw.lower()
            in_title = kw_lower in title_text
            in_meta = kw_lower in meta_text
            in_h1 = any(kw_lower in h.lower() for h in h1s)
            if in_title: score += 2
            if in_meta: score += 1
            if in_h1: score += 2
            keyword_data[kw] = {'count': self.text_content.count(kw_lower), 'in_title': in_title, 'in_meta': in_meta, 'in_h1': in_h1}
        self.add_result('Content & Keywords', 'Keyword Placement', score, len(self.keywords) * 5, keyword_data, [])

        # Image SEO
        images = self.soup.find_all('img')
        missing_alt = [img.get('src', 'N/A') for img in images if not img.get('alt', '').strip()]
        score = int(((len(images) - len(missing_alt)) / len(images)) * 10) if images else 10
        advice = [f"❌ {len(missing_alt)} images are missing descriptive alt text."] if missing_alt else ["✅ All images have alt text."]
        self.add_result('Content & Keywords', 'Image ALT Tags', score, 10, {'count': len(images), 'missing_alt': len(missing_alt)}, advice)

        # Word Count
        score, advice = (5, [f"✅ Good content length ({self.word_count} words)."]) if self.word_count > 300 else (0, [f"🟡 Low word count ({self.word_count} words). Aim for 300+."])
        self.add_result('Content & Keywords', 'Word Count', score, 5, {}, advice)

    def check_technical_seo(self):
        """HTTPS, Viewport, Robots, Sitemap, aur Language check karta hai."""
        # HTTPS
        score, advice = (10, ["✅ Site is served over secure HTTPS."]) if self.url.startswith('https') else (0, ["🔴 Critical: Site is not secure (HTTP)."])
        self.add_result('Technical SEO', 'HTTPS', score, 10, {}, advice)

        # Mobile Viewport
        viewport = self.soup.find('meta', attrs={'name': 'viewport'})
        score, advice = (10, ["✅ Viewport meta tag found, enabling mobile-friendliness."]) if viewport else (0, ["🔴 Missing viewport meta tag. Page will not render well on mobile."])
        self.add_result('Technical SEO', 'Mobile Viewport', score, 10, {}, advice)

        # Robots.txt & Sitemap
        try:
            robots_ok = requests.get(self.url.strip('/') + '/robots.txt', timeout=5).status_code == 200
        except: robots_ok = False
        try:
            sitemap_ok = requests.get(self.url.strip('/') + '/sitemap.xml', timeout=5).status_code == 200
        except: sitemap_ok = False
        score = (5 if robots_ok else 0) + (5 if sitemap_ok else 0)
        advice = [f"{'✅ Found' if robots_ok else '🔴 Not Found'}: robots.txt", f"{'✅ Found' if sitemap_ok else '🔴 Not Found'}: sitemap.xml"]
        self.add_result('Technical SEO', 'Robots & Sitemap', score, 10, {}, advice)

        # Language Declaration
        lang = self.soup.find('html').get('lang') if self.soup.find('html') else None
        score, advice = (5, [f"✅ Language declared: `{lang}`."]) if lang else (0, ["🟡 No `lang` attribute on `<html>` tag."])
        self.add_result('Technical SEO', 'Language Declaration', score, 5, {}, advice)

    def check_links(self):
        """Internal, External, aur Nofollow links check karta hai."""
        all_links = self.soup.find_all("a", href=True)
        internal_links = [a['href'] for a in all_links if self.url in a['href'] or a['href'].startswith(('/', '#'))]
        external_links = [a['href'] for a in all_links if a['href'].startswith('http') and self.url not in a['href']]
        nofollow_links = [a['href'] for a in all_links if a.get('rel') and 'nofollow' in a.get('rel')]
        score = 5 if internal_links and external_links else 0
        advice = ["✅ Good mix of internal and external links found."]
        self.add_result('Link Analysis', 'Link Profile', score, 5, {'total': len(all_links), 'internal': len(internal_links), 'external': len(external_links), 'nofollow': len(nofollow_links)}, advice)

    def check_social_and_schema(self):
        """Social tags (Open Graph, Twitter) aur Structured Data (Schema) check karta hai."""
        # Social Meta Tags
        og_title = self.soup.find('meta', property='og:title')
        og_desc = self.soup.find('meta', property='og:description')
        twitter_card = self.soup.find('meta', attrs={'name': 'twitter:card'})
        score = (5 if og_title and og_desc else 0) + (5 if twitter_card else 0)
        advice = ["✅ Open Graph tags found." if og_title and og_desc else "🟡 Missing Open Graph tags.",
                  "✅ Twitter Card tag found." if twitter_card else "🟡 Missing Twitter Card tag."]
        self.add_result('Social & Schema', 'Social Meta Tags', score, 10, {}, advice)
        
        # Structured Data (Schema)
        schema_scripts = self.soup.find_all('script', type='application/ld+json')
        schema_found = bool(schema_scripts)
        schema_types = []
        if schema_found:
            for script in schema_scripts:
                try:
                    data = json.loads(script.string)
                    schema_types.append(data.get('@type', 'N/A'))
                except (json.JSONDecodeError, AttributeError): continue
        score, advice = (10, [f"✅ Found schema types: `{', '.join(schema_types)}`"]) if schema_found else (0, ["🟡 No JSON-LD structured data found."])
        self.add_result('Social & Schema', 'Structured Data', score, 10, {'found': schema_found, 'types': schema_types}, advice)

    # --- Helper & Reporting Methods ---

    def add_result(self, category, check_name, score, max_score, data, advice):
        """Result ko structure mein add karta hai."""
        if category not in self.results:
            self.results[category] = {}
        self.results[category][check_name] = {'score': score, 'max_score': max_score, 'data': data, 'advice': advice}
        self.total_score += score
        self.max_score += max_score

    def generate_report(self):
        """Final markdown report generate karta hai."""
        print("✍️ Generating Markdown report...")
        history = self.load_history()
        last_score = history[-2][1] if len(history) > 1 else self.total_score
        score_diff = self.total_score - last_score
        trend_arrow = '▲' if score_diff > 0 else '▼' if score_diff < 0 else '▬'
        
        md = f"# 📈 SEO Analysis Report & Dashboard\n\n"
        md += f"**URL:** `{self.url}`  \n"
        md += f"**Date:** `{datetime.datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S UTC')}`  \n"
        md += f"**Overall Score:** `{self.total_score}/{self.max_score}` ({trend_arrow} {score_diff:+})\n\n"
        
        md += "--- \n\n"
        md += "## 📊 At a Glance\n\n"
        md += f'<img src="{os.path.basename(self.score_chart)}" alt="SEO Score" width="250"/>'
        md += f'<img src="{os.path.basename(self.trend_chart)}" alt="SEO Trend" width="500"/>\n\n'

        md += "--- \n\n"
        md += "## 📋 Detailed Analysis\n\n"

        for category, checks in self.results.items():
            cat_score = sum(c['score'] for c in checks.values())
            cat_max_score = sum(c['max_score'] for c in checks.values())
            md += f"<details>\n<summary><strong>{category} - Score: {cat_score}/{cat_max_score}</strong></summary>\n\n"
            md += "| Check | Score | Status | Details & Actionable Advice |\n"
            md += "|---|---|---|---|\n"
            for name, result in checks.items():
                emoji = self.get_score_emoji(result['score'], result['max_score'])
                details_md = self._format_details_for_check(name, result)
                md += f"| **{name}** | `{result['score']}/{result['max_score']}` | {emoji} | {details_md} |\n"
            md += "\n</details>\n\n"
            
        with open(self.report_file, 'w', encoding='utf-8') as f:
            f.write(md)
        print(f"✅ Report saved to {self.report_file}")

    def _format_details_for_check(self, name, result):
        """Har specific check ke liye details ko format karta hai."""
        data = result['data']
        advice = " <br> ".join(result['advice'])
        details = ""
        if name in ['Title Tag', 'Meta Description']:
            details = f"**Text:** `{data['text']}` <br> **Length:** {data['length']}"
        elif name == 'Page Load Time':
            details = f"**Time:** {data['time']}"
        elif name == 'Keyword Placement':
            details = "`Keyword`|`Title`|`Meta`|`H1`\n---|---|---|---\n"
            for kw, d in data.items():
                details += f"`{kw}`|{'✅' if d['in_title'] else '❌'}|{'✅' if d['in_meta'] else '❌'}|{'✅' if d['in_h1'] else '❌'}\n"
        elif name == 'Image ALT Tags':
            details = f"**Total Images:** {data['count']} <br> **Missing Alt:** {data['missing_alt']}"
        elif name == 'Link Profile':
            details = f"**Total:** {data['total']} | **Internal:** {data['internal']} | **External:** {data['external']}"
        return f"{details}<br><br>👉 {advice}"

    def save_history(self):
        """Current score ko history file mein append karta hai."""
        file_exists = os.path.isfile(self.history_file)
        with open(self.history_file, 'a', newline='') as f:
            writer = csv.writer(f)
            if not file_exists:
                writer.writerow(['date', 'score', 'max_score'])
            writer.writerow([datetime.datetime.utcnow().strftime('%Y-%m-%d'), self.total_score, self.max_score])
        print(f"💾 Score history updated in {self.history_file}")

    def load_history(self):
        """History file se score data load karta hai."""
        if not os.path.isfile(self.history_file): return []
        with open(self.history_file, 'r') as f:
            reader = csv.reader(f)
            next(reader) # Skip header
            return [(datetime.datetime.strptime(row[0], '%Y-%m-%d'), int(row[1])) for row in reader]

    def generate_charts(self):
        """Saare visual charts generate karta hai."""
        self.generate_trend_chart()
        self.generate_score_donut_chart()

    def generate_score_donut_chart(self):
        """Overall score ka ek donut chart generate karta hai."""
        print("🎨 Generating score donut chart...")
        score_perc = (self.total_score / self.max_score) * 100 if self.max_score > 0 else 0
        
        fig, ax = plt.subplots(figsize=(4, 4))
        
        if score_perc >= 85: color = '#28a745'
        elif score_perc >= 60: color = '#ffc107'
        else: color = '#dc3545'

        ax.pie([score_perc, 100 - score_perc], startangle=90, colors=[color, '#e9ecef'],
               wedgeprops=dict(width=0.4, edgecolor='w'))
        ax.text(0, 0, f'{self.total_score}\n/{self.max_score}', ha='center', va='center', fontsize=24, weight='bold')
        
        plt.title('Overall SEO Score', fontsize=14, weight='bold')
        plt.tight_layout()
        plt.savefig(self.score_chart, dpi=100, transparent=True)
        plt.close()
        print(f"✅ Donut chart saved to {self.score_chart}")

    def generate_trend_chart(self):
        """Historical score ka trend chart generate karta hai."""
        print("🎨 Generating trend chart...")
        history = self.load_history()
        if len(history) < 2:
            print("⚠️ Not enough data for a trend chart. Need at least 2 runs.")
            if not os.path.exists(self.trend_chart):
                fig, ax = plt.subplots(figsize=(10, 4))
                ax.text(0.5, 0.5, 'Run the bot again to see your score trend.', ha='center', va='center')
                plt.savefig(self.trend_chart); plt.close()
            return

        dates, scores = zip(*history)
        plt.style.use('seaborn-v0_8-whitegrid')
        fig, ax = plt.subplots(figsize=(10, 4))
        ax.plot(dates, scores, marker='o', linestyle='-', color='#007acc', label='SEO Score')
        ax.set_title('SEO Score Trend Over Time', fontsize=16, weight='bold')
        ax.set_ylabel('Score', fontsize=12)
        ax.set_ylim(0, max(self.max_score + 10, max(scores) + 10))
        fig.autofmt_xdate()
        ax.xaxis.set_major_formatter(mdates.DateFormatter('%b %d'))
        plt.tight_layout()
        plt.savefig(self.trend_chart, dpi=100)
        plt.close()
        print(f"✅ Trend chart saved to {self.trend_chart}")

if __name__ == "__main__":
    try:
        bot = SEOAnalyzer(config_path='config.ini')
        if bot.run_analysis():
            bot.save_history()
            bot.generate_charts()
            bot.generate_report()
    except FileNotFoundError as e:
        print(f"❌ Error: {e}")
    except Exception as e:
        print(f"❌ A critical error occurred in the main execution block: {e}")



