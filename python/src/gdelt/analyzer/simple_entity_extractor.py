#!/usr/bin/env python3
"""
Simple Entity Extractor for GDELT News Articles

This module provides a class for extracting named entities from news articles.
It uses a simple rule-based approach that works reliably.
"""

import re
import pandas as pd
import logging
import nltk
from nltk.tokenize import word_tokenize
from collections import Counter, defaultdict

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Try to download NLTK resources
try:
    nltk.download('punkt', quiet=True)
except Exception as e:
    logger.warning(f"Could not download NLTK resources: {e}")

class SimpleEntityExtractor:
    """Class for extracting named entities from text"""
    
    def __init__(self):
        """Initialize the entity extractor"""
        # Store extracted entities for statistics calculation
        self.entities = []
        self.entity_counts = Counter()
        self.entity_sources = defaultdict(set)
        
        # Common organization suffixes
        self.org_suffixes = [
            'Corp', 'Corporation', 'Inc', 'Incorporated', 'LLC', 'Ltd', 'Limited',
            'Co', 'Company', 'Group', 'Holdings', 'Enterprises', 'Partners',
            'Association', 'Foundation', 'Institute', 'University', 'College',
            'School', 'Hospital', 'Bank', 'Airlines', 'Motors', 'Media',
            'Technologies', 'Solutions', 'Systems', 'International', 'Global',
            'Worldwide', 'National', 'Federal', 'State', 'Agency', 'Department',
            'Ministry', 'Committee', 'Commission', 'Council', 'Authority',
            'Party', 'Union', 'Alliance', 'League', 'Federation', 'Organization',
            'Organisation', 'Network', 'Center', 'Centre', 'Industries', 'Services'
        ]
        
        # Common location indicators
        self.loc_indicators = [
            'Street', 'Avenue', 'Road', 'Boulevard', 'Lane', 'Drive', 'Place',
            'Square', 'Court', 'Terrace', 'Park', 'Plaza', 'Bridge', 'River',
            'Lake', 'Ocean', 'Sea', 'Mountain', 'Hill', 'Valley', 'Forest',
            'Desert', 'Island', 'Peninsula', 'Bay', 'Gulf', 'Strait', 'Channel',
            'City', 'Town', 'Village', 'County', 'District', 'Province', 'State',
            'Region', 'Country', 'Nation', 'Republic', 'Kingdom', 'Empire',
            'Continent', 'Territory', 'Area', 'Zone', 'Airport', 'Station',
            'Port', 'Harbor', 'Harbour', 'Beach', 'Coast', 'Shore'
        ]
        
        # Common person titles
        self.person_titles = [
            'Mr', 'Mrs', 'Ms', 'Miss', 'Dr', 'Prof', 'Professor', 'Sir', 'Dame',
            'Lord', 'Lady', 'President', 'Prime Minister', 'Chancellor', 'Minister',
            'Senator', 'Representative', 'Congressman', 'Congresswoman', 'Governor',
            'Mayor', 'Chief', 'Director', 'Chairman', 'Chairwoman', 'CEO', 'CFO',
            'CTO', 'COO', 'VP', 'Manager', 'Supervisor', 'Officer', 'General',
            'Colonel', 'Major', 'Captain', 'Lieutenant', 'Sergeant', 'Private',
            'Judge', 'Justice', 'Attorney', 'Lawyer', 'Doctor', 'Nurse', 'Engineer',
            'Architect', 'Scientist', 'Researcher', 'Teacher', 'Principal', 'Dean',
            'Reverend', 'Pastor', 'Priest', 'Bishop', 'Cardinal', 'Pope', 'Rabbi',
            'Imam', 'Sheikh', 'King', 'Queen', 'Prince', 'Princess', 'Duke', 'Duchess'
        ]
        
        # Common countries and major cities
        self.common_locations = [
            'Afghanistan', 'Albania', 'Algeria', 'Andorra', 'Angola', 'Argentina',
            'Armenia', 'Australia', 'Austria', 'Azerbaijan', 'Bahamas', 'Bahrain',
            'Bangladesh', 'Barbados', 'Belarus', 'Belgium', 'Belize', 'Benin',
            'Bhutan', 'Bolivia', 'Bosnia', 'Botswana', 'Brazil', 'Brunei',
            'Bulgaria', 'Burkina Faso', 'Burundi', 'Cambodia', 'Cameroon',
            'Canada', 'Chad', 'Chile', 'China', 'Colombia', 'Congo', 'Costa Rica',
            'Croatia', 'Cuba', 'Cyprus', 'Czech Republic', 'Denmark', 'Djibouti',
            'Dominican Republic', 'Ecuador', 'Egypt', 'El Salvador', 'England',
            'Eritrea', 'Estonia', 'Ethiopia', 'Fiji', 'Finland', 'France', 'Gabon',
            'Gambia', 'Georgia', 'Germany', 'Ghana', 'Greece', 'Grenada', 'Guatemala',
            'Guinea', 'Guyana', 'Haiti', 'Honduras', 'Hungary', 'Iceland', 'India',
            'Indonesia', 'Iran', 'Iraq', 'Ireland', 'Israel', 'Italy', 'Jamaica',
            'Japan', 'Jordan', 'Kazakhstan', 'Kenya', 'Korea', 'Kosovo', 'Kuwait',
            'Kyrgyzstan', 'Laos', 'Latvia', 'Lebanon', 'Lesotho', 'Liberia', 'Libya',
            'Liechtenstein', 'Lithuania', 'Luxembourg', 'Macedonia', 'Madagascar',
            'Malawi', 'Malaysia', 'Maldives', 'Mali', 'Malta', 'Mauritania',
            'Mauritius', 'Mexico', 'Moldova', 'Monaco', 'Mongolia', 'Montenegro',
            'Morocco', 'Mozambique', 'Myanmar', 'Namibia', 'Nepal', 'Netherlands',
            'New Zealand', 'Nicaragua', 'Niger', 'Nigeria', 'Norway', 'Oman',
            'Pakistan', 'Panama', 'Paraguay', 'Peru', 'Philippines', 'Poland',
            'Portugal', 'Qatar', 'Romania', 'Russia', 'Rwanda', 'Saudi Arabia',
            'Scotland', 'Senegal', 'Serbia', 'Seychelles', 'Sierra Leone', 'Singapore',
            'Slovakia', 'Slovenia', 'Somalia', 'South Africa', 'South Korea', 'Spain',
            'Sri Lanka', 'Sudan', 'Suriname', 'Swaziland', 'Sweden', 'Switzerland',
            'Syria', 'Taiwan', 'Tajikistan', 'Tanzania', 'Thailand', 'Togo',
            'Trinidad', 'Tunisia', 'Turkey', 'Turkmenistan', 'Uganda', 'Ukraine',
            'United Arab Emirates', 'United Kingdom', 'United States', 'Uruguay',
            'Uzbekistan', 'Vatican', 'Venezuela', 'Vietnam', 'Wales', 'Yemen',
            'Zambia', 'Zimbabwe',
            # Major cities
            'New York', 'Los Angeles', 'Chicago', 'Houston', 'Phoenix', 'Philadelphia',
            'San Antonio', 'San Diego', 'Dallas', 'San Jose', 'Austin', 'Jacksonville',
            'San Francisco', 'Columbus', 'Indianapolis', 'Seattle', 'Denver', 'Boston',
            'Washington', 'Nashville', 'Baltimore', 'Oklahoma City', 'Portland',
            'Las Vegas', 'Milwaukee', 'Albuquerque', 'Tucson', 'Fresno', 'Sacramento',
            'Long Beach', 'Kansas City', 'Mesa', 'Atlanta', 'Colorado Springs',
            'Raleigh', 'Omaha', 'Miami', 'Oakland', 'Minneapolis', 'Tulsa', 'Cleveland',
            'Wichita', 'Arlington', 'New Orleans', 'Bakersfield', 'Tampa', 'Honolulu',
            'Aurora', 'Anaheim', 'Santa Ana', 'St. Louis', 'Riverside', 'Corpus Christi',
            'Lexington', 'Pittsburgh', 'Anchorage', 'Stockton', 'Cincinnati', 'St. Paul',
            'Toledo', 'Newark', 'Greensboro', 'Plano', 'Henderson', 'Lincoln', 'Buffalo',
            'Jersey City', 'Chula Vista', 'Fort Wayne', 'Orlando', 'St. Petersburg',
            'Chandler', 'Laredo', 'Norfolk', 'Durham', 'Madison', 'Lubbock', 'Irvine',
            'Winston-Salem', 'Glendale', 'Garland', 'Hialeah', 'Reno', 'Chesapeake',
            'Gilbert', 'Baton Rouge', 'Irving', 'Scottsdale', 'North Las Vegas',
            'Fremont', 'Boise', 'Richmond', 'San Bernardino',
            # International cities
            'Tokyo', 'Delhi', 'Shanghai', 'São Paulo', 'Mexico City', 'Cairo', 'Mumbai',
            'Beijing', 'Dhaka', 'Osaka', 'Karachi', 'Chongqing', 'Istanbul', 'Buenos Aires',
            'Kolkata', 'Lagos', 'Rio de Janeiro', 'Tianjin', 'Kinshasa', 'Guangzhou',
            'Paris', 'Shenzhen', 'Jakarta', 'London', 'Lima', 'Bangkok', 'Hyderabad',
            'Seoul', 'Bangalore', 'Santiago', 'Lahore', 'Chennai', 'Bogotá', 'Nagoya',
            'Johannesburg', 'Berlin', 'Madrid', 'Toronto', 'Sydney', 'Melbourne',
            'Moscow', 'Rome', 'Hong Kong', 'Singapore', 'Dubai', 'Riyadh', 'Baghdad',
            'Tehran', 'Kabul', 'Nairobi', 'Casablanca', 'Accra', 'Addis Ababa',
            'Dar es Salaam', 'Algiers', 'Khartoum', 'Abidjan', 'Amman', 'Beirut',
            'Damascus', 'Hanoi', 'Manila', 'Kuala Lumpur', 'Brussels', 'Vienna',
            'Warsaw', 'Budapest', 'Prague', 'Amsterdam', 'Copenhagen', 'Stockholm',
            'Oslo', 'Helsinki', 'Athens', 'Lisbon', 'Dublin', 'Edinburgh', 'Zurich',
            'Geneva', 'Munich', 'Frankfurt', 'Hamburg', 'Barcelona', 'Milan', 'Naples',
            'Florence', 'Venice', 'Marseille', 'Lyon', 'Manchester', 'Birmingham',
            'Glasgow', 'Liverpool', 'Belfast', 'Cardiff', 'Montreal', 'Vancouver',
            'Calgary', 'Ottawa', 'Quebec City', 'Auckland', 'Wellington', 'Christchurch',
            'Brisbane', 'Perth', 'Adelaide', 'Canberra', 'Hobart'
        ]
        
        # Common organizations
        self.common_organizations = [
            'United Nations', 'World Health Organization', 'European Union', 'NATO',
            'World Bank', 'International Monetary Fund', 'World Trade Organization',
            'Red Cross', 'Amnesty International', 'Greenpeace', 'UNICEF', 'UNESCO',
            'OPEC', 'ASEAN', 'African Union', 'Organization of American States',
            'Commonwealth of Nations', 'Arab League', 'BRICS', 'G7', 'G20',
            'Microsoft', 'Apple', 'Google', 'Amazon', 'Facebook', 'Tesla', 'Twitter',
            'IBM', 'Intel', 'Samsung', 'Sony', 'Toyota', 'Honda', 'Ford', 'BMW',
            'Mercedes-Benz', 'Volkswagen', 'General Motors', 'Coca-Cola', 'PepsiCo',
            'McDonald\'s', 'Starbucks', 'Walmart', 'Target', 'Nike', 'Adidas',
            'Disney', 'Netflix', 'Warner Bros', 'Universal', 'Paramount', 'Fox',
            'CNN', 'BBC', 'NBC', 'CBS', 'ABC', 'MSNBC', 'Fox News', 'Al Jazeera',
            'Reuters', 'Associated Press', 'New York Times', 'Washington Post',
            'Wall Street Journal', 'The Guardian', 'The Times', 'Le Monde',
            'Der Spiegel', 'El País', 'Corriere della Sera', 'Asahi Shimbun',
            'People\'s Daily', 'RT', 'TASS', 'Xinhua', 'Kyodo News', 'Yonhap News',
            'JPMorgan Chase', 'Bank of America', 'Citigroup', 'Wells Fargo',
            'Goldman Sachs', 'Morgan Stanley', 'HSBC', 'Barclays', 'Deutsche Bank',
            'UBS', 'Credit Suisse', 'BNP Paribas', 'Santander', 'Mitsubishi UFJ',
            'Industrial and Commercial Bank of China', 'China Construction Bank',
            'Agricultural Bank of China', 'Bank of China', 'Royal Bank of Canada',
            'Toronto-Dominion Bank', 'Scotiabank', 'Commonwealth Bank of Australia',
            'ANZ', 'Westpac', 'National Australia Bank', 'Standard Bank', 'Absa',
            'FirstRand', 'Nedbank', 'Exxon Mobil', 'Chevron', 'Shell', 'BP',
            'TotalEnergies', 'Eni', 'Gazprom', 'Rosneft', 'PetroChina', 'Sinopec',
            'Saudi Aramco', 'Petrobras', 'Pemex', 'Lukoil', 'Equinor', 'Repsol',
            'Pfizer', 'Johnson & Johnson', 'Roche', 'Novartis', 'Merck', 'GlaxoSmithKline',
            'Sanofi', 'AstraZeneca', 'Bayer', 'Eli Lilly', 'Abbott Laboratories',
            'Amgen', 'Gilead Sciences', 'Bristol-Myers Squibb', 'Biogen', 'Moderna',
            'BioNTech', 'Siemens', 'General Electric', 'Honeywell', 'Mitsubishi Electric',
            'Hitachi', 'Toshiba', 'Panasonic', 'LG Electronics', 'Philips', 'ABB',
            'Schneider Electric', 'Emerson Electric', 'Caterpillar', 'Komatsu',
            'Deere & Company', 'Volvo', 'Airbus', 'Boeing', 'Lockheed Martin',
            'Raytheon Technologies', 'Northrop Grumman', 'BAE Systems', 'Thales',
            'Leonardo', 'Rolls-Royce', 'SpaceX', 'Blue Origin', 'Virgin Galactic',
            'NASA', 'European Space Agency', 'Roscosmos', 'China National Space Administration',
            'Indian Space Research Organisation', 'Japan Aerospace Exploration Agency',
            'FBI', 'CIA', 'NSA', 'MI5', 'MI6', 'Mossad', 'FSB', 'Interpol', 'Europol',
            'Pentagon', 'White House', 'Kremlin', 'Downing Street', 'Élysée Palace',
            'Bundestag', 'Reichstag', 'Capitol Hill', 'Congress', 'Senate', 'House of Representatives',
            'Parliament', 'Supreme Court', 'International Court of Justice', 'International Criminal Court',
            'Harvard University', 'Stanford University', 'MIT', 'Oxford University', 'Cambridge University',
            'Yale University', 'Princeton University', 'Columbia University', 'University of Chicago',
            'California Institute of Technology', 'University of California', 'Imperial College London',
            'ETH Zurich', 'University of Toronto', 'University of Melbourne', 'University of Sydney',
            'Peking University', 'Tsinghua University', 'University of Tokyo', 'Seoul National University',
            'National University of Singapore', 'Nanyang Technological University'
        ]
    
    def extract_entities_from_dataframe(self, df):
        """
        Extract entities from a DataFrame of articles
        
        Args:
            df: DataFrame containing articles with 'title' column
            
        Returns:
            DataFrame containing extracted entities
        """
        logger.info("Extracting entities from DataFrame")
        
        # Reset stored entities
        self.entities = []
        self.entity_counts = Counter()
        self.entity_sources = defaultdict(set)
        
        # Extract entities from each article
        for idx, row in df.iterrows():
            title = row.get('title', '')
            url = row.get('url', '')
            domain = row.get('domain', '')
            
            if pd.isna(title) or title == '':
                continue
            
            # Extract entities from title
            article_entities = self.extract_entities(title)
            
            # Add article URL and domain to each entity
            for entity in article_entities:
                entity['article_url'] = url
                entity['article_domain'] = domain
                entity['context'] = title
                
                # Update entity counts and sources
                entity_key = (entity['text'], entity['type'])
                self.entity_counts[entity_key] += 1
                self.entity_sources[entity_key].add(domain)
                
                # Add to list of all entities
                self.entities.append(entity)
        
        # Convert to DataFrame
        if self.entities:
            entities_df = pd.DataFrame(self.entities)
            logger.info(f"Extracted {len(entities_df)} entities from {len(df)} articles")
            return entities_df
        else:
            logger.warning("No entities extracted")
            return pd.DataFrame()
    
    def calculate_entity_stats(self):
        """
        Calculate statistics for extracted entities
        
        Returns:
            DataFrame containing entity statistics
        """
        logger.info("Calculating entity statistics")
        
        # Create list of entity statistics
        entity_stats = []
        
        for (entity_text, entity_type), count in self.entity_counts.items():
            sources = self.entity_sources[(entity_text, entity_type)]
            
            # Calculate source diversity (0-1 scale)
            source_diversity = len(sources) / count if count > 0 else 0
            
            # Calculate trust score (0-1 scale)
            # Higher if mentioned by more sources and more times
            trust_score = min(1.0, (len(sources) * 0.5 + count * 0.1) / 5)
            
            entity_stat = {
                'entity': entity_text,
                'type': entity_type,
                'count': count,
                'num_sources': len(sources),
                'source_diversity': source_diversity,
                'trust_score': trust_score
            }
            
            entity_stats.append(entity_stat)
        
        # Convert to DataFrame
        if entity_stats:
            stats_df = pd.DataFrame(entity_stats)
            logger.info(f"Calculated statistics for {len(stats_df)} entities")
            return stats_df
        else:
            logger.warning("No entity statistics calculated")
            return pd.DataFrame()
    
    def extract_entities(self, text):
        """
        Extract named entities from text
        
        Args:
            text: Text to extract entities from
            
        Returns:
            List of dictionaries with entity information
        """
        if pd.isna(text) or text == '':
            return []
        
        entities = []
        
        # Extract organizations
        org_entities = self._extract_organizations(text)
        entities.extend(org_entities)
        
        # Extract locations
        loc_entities = self._extract_locations(text)
        entities.extend(loc_entities)
        
        # Extract persons
        person_entities = self._extract_persons(text)
        entities.extend(person_entities)
        
        # Remove duplicates (same text and type)
        unique_entities = {}
        for entity in entities:
            key = (entity['text'], entity['type'])
            if key not in unique_entities:
                unique_entities[key] = entity
        
        return list(unique_entities.values())
    
    def _extract_organizations(self, text):
        """Extract organization entities"""
        entities = []
        
        # Extract common organizations
        for org in self.common_organizations:
            if org in text:
                entity = {
                    'text': org,
                    'type': 'ORGANIZATION',
                    'start': text.find(org),
                    'end': text.find(org) + len(org),
                    'method': 'simple'
                }
                entities.append(entity)
        
        # Extract organizations with common suffixes
        # Pattern: 1-3 capitalized words followed by a known organization suffix
        pattern = r'\b([A-Z][a-z]+(?:\s+[A-Z][a-z]+){0,2}\s+(?:' + '|'.join(self.org_suffixes) + r'))\b'
        for match in re.finditer(pattern, text):
            entity = {
                'text': match.group(0),
                'type': 'ORGANIZATION',
                'start': match.start(),
                'end': match.end(),
                'method': 'simple'
            }
            entities.append(entity)
        
        return entities
    
    def _extract_locations(self, text):
        """Extract location entities"""
        entities = []
        
        # Extract common locations
        for loc in self.common_locations:
            if loc in text:
                entity = {
                    'text': loc,
                    'type': 'LOCATION',
                    'start': text.find(loc),
                    'end': text.find(loc) + len(loc),
                    'method': 'simple'
                }
                entities.append(entity)
        
        # Extract locations with common indicators
        # Pattern: 1-2 capitalized words followed by a known location indicator
        pattern = r'\b([A-Z][a-z]+(?:\s+[A-Z][a-z]+)?\s+(?:' + '|'.join(self.loc_indicators) + r'))\b'
        for match in re.finditer(pattern, text):
            entity = {
                'text': match.group(0),
                'type': 'LOCATION',
                'start': match.start(),
                'end': match.end(),
                'method': 'simple'
            }
            entities.append(entity)
        
        return entities
    
    def _extract_persons(self, text):
        """Extract person entities"""
        entities = []
        
        # Extract persons with titles
        # Pattern: Title followed by 1-3 capitalized words
        pattern = r'\b(?:' + '|'.join(self.person_titles) + r')\.\s+([A-Z][a-z]+(?:\s+[A-Z][a-z]+){0,2})\b'
        for match in re.finditer(pattern, text):
            entity = {
                'text': match.group(0),
                'type': 'PERSON',
                'start': match.start(),
                'end': match.end(),
                'method': 'simple'
            }
            entities.append(entity)
        
        # Extract capitalized names (2-3 words)
        # This is more prone to false positives, so we'll be conservative
        pattern = r'\b([A-Z][a-z]+\s+[A-Z][a-z]+(?:\s+[A-Z][a-z]+)?)\b'
        for match in re.finditer(pattern, text):
            # Skip if it's already in common locations or organizations
            name = match.group(0)
            if name in self.common_locations or name in self.common_organizations:
                continue
                
            # Skip if it contains location indicators or organization suffixes
            skip = False
            for suffix in self.org_suffixes:
                if suffix in name:
                    skip = True
                    break
            for indicator in self.loc_indicators:
                if indicator in name:
                    skip = True
                    break
            if skip:
                continue
            
            entity = {
                'text': name,
                'type': 'PERSON',
                'start': match.start(),
                'end': match.end(),
                'method': 'simple'
            }
            entities.append(entity)
        
        return entities
