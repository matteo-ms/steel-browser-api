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
            
            return data
        except Exception as e:
            raise Exception(f"Failed to create session: {str(e)}")
    
    def release_session(self):
        """Release the browser session"""
        if not self.session_id:
            return
            
        try:
            response = requests.post(
                f"{self.steel_url}/v1/sessions/{self.session_id}/release",
                headers={'Content-Type': 'application/json'},
                timeout=30  # 30 seconds for release
            )
            response.raise_for_status()
        except Exception as e:
            print(f"Warning: Failed to release session: {e}")
    
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
        search_url = self.build_google_url(query, language, region, search_type, time_filter)
        
        # Create session
        self.create_session()
        
        all_results = []
        
        async with async_playwright() as p:
            try:
                # Connect to Steel Browser
                browser = await p.chromium.connect_over_cdp(self.websocket_url)
                
                # Get or create context and page
                contexts = browser.contexts
                if contexts:
                    context = contexts[0]
                    pages = context.pages
                    page = pages[0] if pages else await context.new_page()
                else:
                    context = await browser.new_context()
                    page = await context.new_page()
                
                # Navigate to search URL
                await page.goto(search_url, timeout=180000)  # 3 minutes
                await page.wait_for_timeout(2000)
                
                # Handle cookie consent
                cookie_buttons = [
                    'button:has-text("Accetta tutto")',
                    'button:has-text("Accept all")',
                    'button:has-text("Alles accepteren")',
                    'button[id="L2AGLb"]',
                ]
                
                for button_selector in cookie_buttons:
                    try:
                        await page.click(button_selector, timeout=2000)
                        await page.wait_for_timeout(1000)
                        break
                    except:
                        continue
                
                # Wait for results
                try:
                    await page.wait_for_selector('#search', timeout=180000)  # 3 minutes
                except:
                    try:
                        await page.wait_for_selector('#rso', timeout=180000)  # 3 minutes
                    except:
                        await page.wait_for_load_state('networkidle', timeout=180000)  # 3 minutes
                
                # Extract search results
                if search_type == 'news':
                    title_elements = await page.query_selector_all('div[role="heading"]')
                else:
                    title_elements = await page.query_selector_all('h3')
                
                search_results = []
                for title_elem in title_elements[:num_results]:
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
                        
                        if len(search_results) >= num_results:
                            break
                    except Exception as e:
                        continue
                
                # Deep scrape each result
                for i, result in enumerate(search_results, 1):
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
                    
                    # Small delay between requests
                    await page.wait_for_timeout(2000)
                
                # Close browser
                await browser.close()
                
                return all_results
                
            except Exception as e:
                raise Exception(f"Scraping failed: {str(e)}")
            finally:
                # Release session
                self.release_session()
    
    async def extract_page_content(self, page, url, position):
        """Extract main content from a page"""
        try:
            await page.goto(url, wait_until='domcontentloaded', timeout=180000)  # 3 minutes
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
            try:
                content['title'] = await page.title()
            except:
                pass
            
            # Find main content
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
                        break
                except:
                    continue
            
            if not main_content:
                main_content = await page.query_selector('body')
            
            if main_content:
                # Extract headings
                h_elements = await main_content.query_selector_all('h1, h2, h3, h4')
                for h in h_elements[:30]:
                    try:
                        heading_text = await h.inner_text()
                        if heading_text and len(heading_text.strip()) > 0:
                            content['headings'].append(heading_text.strip())
                    except:
                        pass
                
                # Extract paragraphs
                p_elements = await main_content.query_selector_all('p')
                for p in p_elements[:50]:
                    try:
                        p_text = await p.inner_text()
                        if p_text and len(p_text.strip()) > 20:
                            content['paragraphs'].append(p_text.strip())
                    except:
                        pass
                
                # Get all text
                try:
                    main_text = await main_content.inner_text()
                    content['main_text'] = main_text[:20000]  # Limit to 20k chars
                except:
                    pass
            
            # Extract metadata
            try:
                meta_desc = await page.query_selector('meta[name="description"]')
                if meta_desc:
                    content['metadata']['description'] = await meta_desc.get_attribute('content')
            except:
                pass
            
            return content
            
        except Exception as e:
            return {
                'url': url,
                'error': str(e),
                'title': '',
                'main_text': '',
                'headings': [],
                'paragraphs': []
            }

