"""
Steel Browser Scraper Module
Core scraping logic for search and deep content extraction
"""

import asyncio
from playwright.async_api import async_playwright
import requests
import json
from datetime import datetime


class SteelBrowserScraper:
    def __init__(self, steel_url):
        self.steel_url = steel_url.rstrip('/')
        self.session_id = None
        self.websocket_url = None
        
    def create_session(self):
        """Create a new browser session on Steel Browser"""
        try:
            print(f"[LOG] Creating session with Steel Browser at {self.steel_url}")
            response = requests.post(
                f"{self.steel_url}/v1/sessions",
                headers={'Content-Type': 'application/json'},
                json={},
                timeout=180  # 3 minutes
            )
            response.raise_for_status()
            data = response.json()
            
            self.session_id = data.get('id')
            self.websocket_url = data.get('websocketUrl')
            
            print(f"[LOG] ✓ Session created successfully: {self.session_id}")
            print(f"[LOG] WebSocket URL: {self.websocket_url}")
            
            return data
        except Exception as e:
            print(f"[ERROR] Failed to create session: {str(e)}")
            raise Exception(f"Failed to create session: {str(e)}")
    
    def release_session(self):
        """Release the browser session"""
        if not self.session_id:
            print(f"[LOG] No session to release")
            return
            
        try:
            print(f"[LOG] Releasing session: {self.session_id}")
            response = requests.post(
                f"{self.steel_url}/v1/sessions/{self.session_id}/release",
                headers={'Content-Type': 'application/json'},
                timeout=30  # 30 seconds for release
            )
            response.raise_for_status()
            print(f"[LOG] ✓ Session released successfully")
        except Exception as e:
            print(f"[WARNING] Failed to release session: {e}")
    
    def build_google_url(self, query, language='it', region='it', search_type='web', time_filter=None):
        """Build Google search URL with filters"""
        base_url = "https://www.google.com/search"
        
        params = {
            'q': query,
            'hl': language,
            'lr': f'lang_{language}',
            'gl': region,
        }
        
        if search_type == 'news':
            params['tbm'] = 'nws'
        
        if time_filter:
            time_map = {
                'hour': 'qdr:h',
                'day': 'qdr:d',
                '3days': 'qdr:d3',
                'week': 'qdr:w',
                'month': 'qdr:m',
                'year': 'qdr:y'
            }
            if time_filter in time_map:
                params['tbs'] = time_map[time_filter]
        
        param_string = '&'.join([f'{k}={requests.utils.quote(str(v))}' for k, v in params.items()])
        return f"{base_url}?{param_string}"
    
    async def search_and_extract(self, query, language='it', region='it', 
                                 search_type='web', time_filter=None, num_results=5):
        """
        Complete workflow: Search + Deep scrape each result
        """
        print(f"\n[LOG] ========== STARTING SEARCH AND EXTRACT ==========")
        print(f"[LOG] Query: {query}")
        print(f"[LOG] Language: {language}, Region: {region}")
        print(f"[LOG] Search Type: {search_type}, Time Filter: {time_filter}")
        print(f"[LOG] Num Results: {num_results}")
        
        search_url = self.build_google_url(query, language, region, search_type, time_filter)
        print(f"[LOG] Google URL: {search_url}")
        
        # Create session
        print(f"[LOG] Step 1: Creating browser session...")
        self.create_session()
        
        all_results = []
        
        async with async_playwright() as p:
            try:
                # Connect to Steel Browser
                print(f"[LOG] Step 2: Connecting to browser via CDP...")
                browser = await p.chromium.connect_over_cdp(self.websocket_url)
                print(f"[LOG] ✓ Connected to browser successfully")
                
                # Get or create context and page
                print(f"[LOG] Step 3: Getting browser context and page...")
                contexts = browser.contexts
                if contexts:
                    context = contexts[0]
                    pages = context.pages
                    page = pages[0] if pages else await context.new_page()
                    print(f"[LOG] ✓ Using existing context")
                else:
                    context = await browser.new_context()
                    page = await context.new_page()
                    print(f"[LOG] ✓ Created new context")
                
                # Navigate to search URL
                print(f"[LOG] Step 4: Navigating to Google search page...")
                await page.goto(search_url, timeout=180000)  # 3 minutes
                print(f"[LOG] ✓ Page loaded successfully")
                await page.wait_for_timeout(2000)
                
                # Handle cookie consent
                print(f"[LOG] Step 5: Handling cookie consent...")
                cookie_buttons = [
                    'button:has-text("Accetta tutto")',
                    'button:has-text("Accept all")',
                    'button:has-text("Alles accepteren")',
                    'button[id="L2AGLb"]',
                ]
                
                cookie_accepted = False
                for button_selector in cookie_buttons:
                    try:
                        await page.click(button_selector, timeout=2000)
                        await page.wait_for_timeout(1000)
                        print(f"[LOG] ✓ Cookie consent accepted with: {button_selector}")
                        cookie_accepted = True
                        break
                    except:
                        continue
                
                if not cookie_accepted:
                    print(f"[LOG] No cookie consent button found (already accepted or not present)")
                
                # Wait for results
                print(f"[LOG] Step 6: Waiting for search results to load...")
                try:
                    await page.wait_for_selector('#search', timeout=180000)  # 3 minutes
                    print(f"[LOG] ✓ Search results loaded (#search selector)")
                except:
                    try:
                        await page.wait_for_selector('#rso', timeout=180000)  # 3 minutes
                        print(f"[LOG] ✓ Search results loaded (#rso selector)")
                    except:
                        await page.wait_for_load_state('networkidle', timeout=180000)  # 3 minutes
                        print(f"[LOG] ✓ Page reached network idle state")
                
                # Extract search results
                print(f"[LOG] Step 7: Extracting search result URLs...")
                if search_type == 'news':
                    title_elements = await page.query_selector_all('div[role="heading"]')
                    print(f"[LOG] Found {len(title_elements)} news title elements")
                else:
                    title_elements = await page.query_selector_all('h3')
                    print(f"[LOG] Found {len(title_elements)} h3 title elements")
                
                search_results = []
                for idx, title_elem in enumerate(title_elements[:num_results * 2], 1):  # Try more elements
                    try:
                        title = await title_elem.inner_text()
                        if not title or len(title.strip()) == 0:
                            continue
                        
                        parent_link = await title_elem.evaluate_handle('element => element.closest("a")')
                        if not parent_link:
                            continue
                        
                        url = await parent_link.evaluate('(element) => element.href')
                        if not url or not url.startswith('http'):
                            continue
                        
                        search_results.append({
                            'title': title.strip(),
                            'url': url
                        })
                        print(f"[LOG] ✓ Extracted URL {len(search_results)}: {title[:60]}...")
                        
                        if len(search_results) >= num_results:
                            break
                    except Exception as e:
                        print(f"[LOG] Skipping element {idx}: {str(e)[:50]}")
                        continue
                
                print(f"[LOG] ✓ Total URLs extracted: {len(search_results)}")
                
                # Deep scrape each result
                print(f"\n[LOG] Step 8: Starting deep scrape of {len(search_results)} pages...")
                for i, result in enumerate(search_results, 1):
                    print(f"\n[LOG] --- Scraping page {i}/{len(search_results)} ---")
                    print(f"[LOG] Title: {result['title'][:60]}...")
                    print(f"[LOG] URL: {result['url']}")
                    
                    content = await self.extract_page_content(page, result['url'], i)
                    
                    # Combine search data with scraped content
                    full_data = {
                        'position': i,
                        'search_title': result['title'],
                        'url': result['url'],
                        'page_title': content.get('title', ''),
                        'headings': content.get('headings', []),
                        'paragraphs': content.get('paragraphs', []),
                        'main_text': content.get('main_text', ''),
                        'metadata': content.get('metadata', {}),
                        'error': content.get('error', None),
                        'scraped_at': datetime.now().isoformat()
                    }
                    
                    all_results.append(full_data)
                    print(f"[LOG] ✓ Page {i} scraped successfully")
                    
                    # Small delay between requests
                    await page.wait_for_timeout(2000)
                
                # Close browser
                print(f"\n[LOG] Step 9: Closing browser...")
                await browser.close()
                print(f"[LOG] ✓ Browser closed")
                
                print(f"\n[LOG] ========== SCRAPING COMPLETED ==========")
                print(f"[LOG] Total results scraped: {len(all_results)}")
                
                return all_results
                
            except Exception as e:
                print(f"\n[ERROR] ========== SCRAPING FAILED ==========")
                print(f"[ERROR] Error: {str(e)}")
                import traceback
                print(f"[ERROR] Traceback:\n{traceback.format_exc()}")
                raise Exception(f"Scraping failed: {str(e)}")
            finally:
                # Release session
                print(f"\n[LOG] Step 10: Cleanup - Releasing session...")
                self.release_session()
    
    async def extract_page_content(self, page, url, position):
        """Extract main content from a page"""
        try:
            print(f"  [LOG] Navigating to page {position}...")
            await page.goto(url, wait_until='domcontentloaded', timeout=180000)  # 3 minutes
            print(f"  [LOG] ✓ Page {position} loaded")
            await page.wait_for_timeout(3000)
            
            content = {
                'url': url,
                'title': '',
                'main_text': '',
                'headings': [],
                'paragraphs': [],
                'metadata': {}
            }
            
            # Get page title
            print(f"  [LOG] Extracting page title...")
            try:
                content['title'] = await page.title()
                print(f"  [LOG] ✓ Title: {content['title'][:50]}...")
            except Exception as e:
                print(f"  [LOG] ⚠ Could not extract title: {str(e)[:30]}")
                pass
            
            # Find main content
            print(f"  [LOG] Finding main content container...")
            main_selectors = [
                'article',
                'main',
                '[role="main"]',
                '.article-content',
                '.post-content',
                '.content',
                '#content',
                '.article-body',
                '.entry-content'
            ]
            
            main_content = None
            for selector in main_selectors:
                try:
                    main_content = await page.query_selector(selector)
                    if main_content:
                        print(f"  [LOG] ✓ Found main content with selector: {selector}")
                        break
                except:
                    continue
            
            if not main_content:
                main_content = await page.query_selector('body')
                print(f"  [LOG] Using body as main content")
            
            if main_content:
                # Extract headings
                print(f"  [LOG] Extracting headings...")
                h_elements = await main_content.query_selector_all('h1, h2, h3, h4')
                for h in h_elements[:30]:
                    try:
                        heading_text = await h.inner_text()
                        if heading_text and len(heading_text.strip()) > 0:
                            content['headings'].append(heading_text.strip())
                    except:
                        pass
                print(f"  [LOG] ✓ Found {len(content['headings'])} headings")
                
                # Extract paragraphs
                print(f"  [LOG] Extracting paragraphs...")
                p_elements = await main_content.query_selector_all('p')
                for p in p_elements[:50]:
                    try:
                        p_text = await p.inner_text()
                        if p_text and len(p_text.strip()) > 20:
                            content['paragraphs'].append(p_text.strip())
                    except:
                        pass
                print(f"  [LOG] ✓ Found {len(content['paragraphs'])} paragraphs")
                
                # Get all text
                print(f"  [LOG] Extracting full text...")
                try:
                    main_text = await main_content.inner_text()
                    content['main_text'] = main_text[:20000]  # Limit to 20k chars
                    print(f"  [LOG] ✓ Extracted {len(main_text)} characters (stored: {len(content['main_text'])})")
                except Exception as e:
                    print(f"  [LOG] ⚠ Could not extract text: {str(e)[:30]}")
                    pass
            
            # Extract metadata
            print(f"  [LOG] Extracting metadata...")
            try:
                meta_desc = await page.query_selector('meta[name="description"]')
                if meta_desc:
                    content['metadata']['description'] = await meta_desc.get_attribute('content')
                    print(f"  [LOG] ✓ Found meta description")
            except:
                pass
            
            print(f"  [LOG] ✓ Content extraction complete for page {position}")
            return content
            
        except Exception as e:
            print(f"  [ERROR] Failed to extract content from page {position}: {str(e)}")
            import traceback
            print(f"  [ERROR] Traceback: {traceback.format_exc()[:200]}")
            return {
                'url': url,
                'error': str(e),
                'title': '',
                'main_text': '',
                'headings': [],
                'paragraphs': []
            }

