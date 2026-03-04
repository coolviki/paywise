import React, { useState, useEffect, useMemo } from 'react';
import { useNavigate } from 'react-router-dom';
import { ArrowLeft, Globe } from 'lucide-react';
import { SearchBar } from '../components/search/SearchBar';
import { PlacesList } from '../components/search/PlacesList';
import { Loading } from '../components/common/Loading';
import { useLocation } from '../hooks/useLocation';
import { useSearch } from '../hooks/useRecommendation';
import { Merchant } from '../types';

// Helper to create portal entry
const portal = (id: string, name: string, category: string): Merchant => ({
  id: `online-${id}`,
  name,
  category,
  logo_url: undefined,
  is_chain: true,
  locations: [],
  offer_count: 0,
});

// Comprehensive list of online portals in India (1000+)
const ONLINE_PORTALS: Merchant[] = [
  // ===== E-COMMERCE & ONLINE SHOPPING =====
  portal('amazon', 'Amazon', 'Online Shopping'),
  portal('flipkart', 'Flipkart', 'Online Shopping'),
  portal('meesho', 'Meesho', 'Online Shopping'),
  portal('snapdeal', 'Snapdeal', 'Online Shopping'),
  portal('shopclues', 'ShopClues', 'Online Shopping'),
  portal('paytmmall', 'Paytm Mall', 'Online Shopping'),
  portal('tatacliq', 'Tata CLiQ', 'Online Shopping'),
  portal('reliancedigital', 'Reliance Digital', 'Online Shopping'),
  portal('croma', 'Croma', 'Electronics'),
  portal('vijaysales', 'Vijay Sales', 'Electronics'),
  portal('poorvika', 'Poorvika', 'Electronics'),
  portal('jiomart', 'JioMart', 'Online Shopping'),
  portal('shoppersstop', 'Shoppers Stop', 'Online Shopping'),
  portal('lifestyle', 'Lifestyle', 'Online Shopping'),
  portal('westside', 'Westside', 'Online Shopping'),
  portal('max', 'Max Fashion', 'Online Shopping'),
  portal('pantaloons', 'Pantaloons', 'Online Shopping'),
  portal('central', 'Central', 'Online Shopping'),
  portal('brandsforyou', 'Brands For You', 'Online Shopping'),
  portal('infibeam', 'Infibeam', 'Online Shopping'),
  portal('industrybuying', 'IndustryBuying', 'Online Shopping'),
  portal('moglix', 'Moglix', 'Online Shopping'),
  portal('indiamart', 'IndiaMart', 'B2B Shopping'),
  portal('tradeindia', 'TradeIndia', 'B2B Shopping'),
  portal('alibaba', 'Alibaba', 'Online Shopping'),
  portal('aliexpress', 'AliExpress', 'Online Shopping'),
  portal('ebay', 'eBay', 'Online Shopping'),
  portal('wish', 'Wish', 'Online Shopping'),
  portal('shein', 'SHEIN', 'Online Shopping'),
  portal('temu', 'Temu', 'Online Shopping'),

  // ===== FASHION & APPAREL =====
  portal('myntra', 'Myntra', 'Fashion'),
  portal('ajio', 'AJIO', 'Fashion'),
  portal('nykaa-fashion', 'Nykaa Fashion', 'Fashion'),
  portal('koovs', 'Koovs', 'Fashion'),
  portal('jabong', 'Jabong', 'Fashion'),
  portal('limeroad', 'LimeRoad', 'Fashion'),
  portal('voonik', 'Voonik', 'Fashion'),
  portal('stalkbuylove', 'StalkBuyLove', 'Fashion'),
  portal('bewakoof', 'Bewakoof', 'Fashion'),
  portal('souledstore', 'The Souled Store', 'Fashion'),
  portal('hlculturestudio', 'H&M', 'Fashion'),
  portal('zara', 'Zara', 'Fashion'),
  portal('uniqlo', 'Uniqlo', 'Fashion'),
  portal('forever21', 'Forever 21', 'Fashion'),
  portal('mango', 'Mango', 'Fashion'),
  portal('marksandspencer', 'Marks & Spencer', 'Fashion'),
  portal('gap', 'GAP', 'Fashion'),
  portal('levis', "Levi's", 'Fashion'),
  portal('pepe', 'Pepe Jeans', 'Fashion'),
  portal('wrangler', 'Wrangler', 'Fashion'),
  portal('lee', 'Lee', 'Fashion'),
  portal('uspoloassn', 'U.S. Polo Assn.', 'Fashion'),
  portal('tommyhilfiger', 'Tommy Hilfiger', 'Fashion'),
  portal('calvinklein', 'Calvin Klein', 'Fashion'),
  portal('adidas', 'Adidas', 'Fashion'),
  portal('nike', 'Nike', 'Fashion'),
  portal('puma', 'Puma', 'Fashion'),
  portal('reebok', 'Reebok', 'Fashion'),
  portal('skechers', 'Skechers', 'Footwear'),
  portal('bata', 'Bata', 'Footwear'),
  portal('metro', 'Metro Shoes', 'Footwear'),
  portal('liberty', 'Liberty Shoes', 'Footwear'),
  portal('woodland', 'Woodland', 'Footwear'),
  portal('redtape', 'Red Tape', 'Footwear'),
  portal('clarks', 'Clarks', 'Footwear'),
  portal('crocs', 'Crocs', 'Footwear'),
  portal('asics', 'ASICS', 'Footwear'),
  portal('newbalance', 'New Balance', 'Footwear'),
  portal('fila', 'FILA', 'Footwear'),
  portal('fabindia', 'FabIndia', 'Fashion'),
  portal('biba', 'BIBA', 'Fashion'),
  portal('wforwoman', 'W for Woman', 'Fashion'),
  portal('aurelia', 'Aurelia', 'Fashion'),
  portal('libas', 'Libas', 'Fashion'),
  portal('global-desi', 'Global Desi', 'Fashion'),
  portal('AND', 'AND', 'Fashion'),
  portal('only', 'ONLY', 'Fashion'),
  portal('vero-moda', 'Vero Moda', 'Fashion'),
  portal('jack-jones', 'Jack & Jones', 'Fashion'),
  portal('selected', 'Selected Homme', 'Fashion'),
  portal('roadster', 'Roadster', 'Fashion'),
  portal('hrx', 'HRX', 'Fashion'),
  portal('wrogn', 'WROGN', 'Fashion'),
  portal('allen-solly', 'Allen Solly', 'Fashion'),
  portal('van-heusen', 'Van Heusen', 'Fashion'),
  portal('louis-philippe', 'Louis Philippe', 'Fashion'),
  portal('peter-england', 'Peter England', 'Fashion'),
  portal('raymond', 'Raymond', 'Fashion'),
  portal('park-avenue', 'Park Avenue', 'Fashion'),
  portal('arrow', 'Arrow', 'Fashion'),
  portal('blackberrys', 'Blackberrys', 'Fashion'),
  portal('indian-terrain', 'Indian Terrain', 'Fashion'),
  portal('flying-machine', 'Flying Machine', 'Fashion'),
  portal('numero-uno', 'Numero Uno', 'Fashion'),
  portal('mufti', 'Mufti', 'Fashion'),
  portal('spykar', 'Spykar', 'Fashion'),
  portal('killer', 'Killer', 'Fashion'),
  portal('duke', 'Duke', 'Fashion'),
  portal('monte-carlo', 'Monte Carlo', 'Fashion'),
  portal('turtle', 'Turtle', 'Fashion'),
  portal('oxemberg', 'Oxemberg', 'Fashion'),
  portal('siyarams', 'Siyarams', 'Fashion'),
  portal('grasim', 'Grasim', 'Fashion'),
  portal('bombay-dyeing', 'Bombay Dyeing', 'Fashion'),
  portal('jockey', 'Jockey', 'Fashion'),
  portal('enamor', 'Enamor', 'Fashion'),
  portal('amante', 'Amante', 'Fashion'),
  portal('zivame', 'Zivame', 'Fashion'),
  portal('clovia', 'Clovia', 'Fashion'),
  portal('prettysecrets', 'PrettySecrets', 'Fashion'),

  // ===== BEAUTY & WELLNESS =====
  portal('nykaa', 'Nykaa', 'Beauty & Wellness'),
  portal('purplle', 'Purplle', 'Beauty & Wellness'),
  portal('myglamm', 'MyGlamm', 'Beauty & Wellness'),
  portal('smytten', 'Smytten', 'Beauty & Wellness'),
  portal('thechannel46', 'The Channel 46', 'Beauty & Wellness'),
  portal('sephora', 'Sephora', 'Beauty & Wellness'),
  portal('themancompany', 'The Man Company', 'Beauty & Wellness'),
  portal('beardo', 'Beardo', 'Beauty & Wellness'),
  portal('ustraa', 'Ustraa', 'Beauty & Wellness'),
  portal('bombay-shaving', 'Bombay Shaving Company', 'Beauty & Wellness'),
  portal('mamaearth', 'Mamaearth', 'Beauty & Wellness'),
  portal('wow', 'WOW Skin Science', 'Beauty & Wellness'),
  portal('plum', 'Plum Goodness', 'Beauty & Wellness'),
  portal('mcaffeine', 'mCaffeine', 'Beauty & Wellness'),
  portal('dotandkey', 'Dot & Key', 'Beauty & Wellness'),
  portal('minimalist', 'Minimalist', 'Beauty & Wellness'),
  portal('sugarcosm', 'Sugar Cosmetics', 'Beauty & Wellness'),
  portal('colorbar', 'Colorbar', 'Beauty & Wellness'),
  portal('lakme', 'Lakme', 'Beauty & Wellness'),
  portal('maybelline', 'Maybelline', 'Beauty & Wellness'),
  portal('loreal', "L'Oreal", 'Beauty & Wellness'),
  portal('mac', 'MAC', 'Beauty & Wellness'),
  portal('kaybeauty', 'Kay Beauty', 'Beauty & Wellness'),
  portal('bodyshop', 'The Body Shop', 'Beauty & Wellness'),
  portal('kiehl', "Kiehl's", 'Beauty & Wellness'),
  portal('clinique', 'Clinique', 'Beauty & Wellness'),
  portal('esteelauder', 'Estee Lauder', 'Beauty & Wellness'),
  portal('forest-essentials', 'Forest Essentials', 'Beauty & Wellness'),
  portal('kama-ayurveda', 'Kama Ayurveda', 'Beauty & Wellness'),
  portal('biotique', 'Biotique', 'Beauty & Wellness'),
  portal('himalaya', 'Himalaya', 'Beauty & Wellness'),
  portal('patanjali', 'Patanjali', 'Beauty & Wellness'),
  portal('khadi-natural', 'Khadi Natural', 'Beauty & Wellness'),
  portal('lenskart', 'Lenskart', 'Eyewear'),
  portal('coolwinks', 'Coolwinks', 'Eyewear'),
  portal('titan-eye', 'Titan Eye Plus', 'Eyewear'),
  portal('johnjacobs', 'John Jacobs', 'Eyewear'),
  portal('vincent-chase', 'Vincent Chase', 'Eyewear'),

  // ===== FOOD DELIVERY =====
  portal('swiggy', 'Swiggy', 'Food Delivery'),
  portal('zomato', 'Zomato', 'Food Delivery'),
  portal('eatsure', 'EatSure', 'Food Delivery'),
  portal('magicpin', 'Magicpin', 'Food Delivery'),
  portal('dunzo', 'Dunzo', 'Food Delivery'),
  portal('box8', 'Box8', 'Food Delivery'),
  portal('faasos', 'Faasos', 'Food Delivery'),
  portal('behrouz', 'Behrouz Biryani', 'Food Delivery'),
  portal('ovenstory', 'Ovenstory Pizza', 'Food Delivery'),
  portal('lunchbox', 'Lunchbox', 'Food Delivery'),
  portal('fasoos', 'Fasoos', 'Food Delivery'),
  portal('dominos', "Domino's", 'Food Delivery'),
  portal('pizzahut', 'Pizza Hut', 'Food Delivery'),
  portal('mcdonalds', "McDonald's", 'Food Delivery'),
  portal('burgerking', 'Burger King', 'Food Delivery'),
  portal('kfc', 'KFC', 'Food Delivery'),
  portal('subway', 'Subway', 'Food Delivery'),
  portal('starbucks', 'Starbucks', 'Food Delivery'),
  portal('ccd', 'Cafe Coffee Day', 'Food Delivery'),
  portal('barista', 'Barista', 'Food Delivery'),
  portal('chaayos', 'Chaayos', 'Food Delivery'),
  portal('chai-point', 'Chai Point', 'Food Delivery'),
  portal('wow-momo', 'Wow! Momo', 'Food Delivery'),
  portal('haldirams', "Haldiram's", 'Food Delivery'),
  portal('bikanervala', 'Bikanervala', 'Food Delivery'),
  portal('naturals', 'Naturals Ice Cream', 'Food Delivery'),
  portal('baskin-robbins', 'Baskin Robbins', 'Food Delivery'),
  portal('keventers', 'Keventers', 'Food Delivery'),

  // ===== GROCERY =====
  portal('bigbasket', 'BigBasket', 'Grocery'),
  portal('blinkit', 'Blinkit', 'Grocery'),
  portal('zepto', 'Zepto', 'Grocery'),
  portal('instamart', 'Swiggy Instamart', 'Grocery'),
  portal('grofers', 'Grofers', 'Grocery'),
  portal('amazon-fresh', 'Amazon Fresh', 'Grocery'),
  portal('flipkart-grocery', 'Flipkart Grocery', 'Grocery'),
  portal('dmart', 'DMart Ready', 'Grocery'),
  portal('spencers', "Spencer's", 'Grocery'),
  portal('more', 'More', 'Grocery'),
  portal('star-bazaar', 'Star Bazaar', 'Grocery'),
  portal('reliance-fresh', 'Reliance Fresh', 'Grocery'),
  portal('nature-basket', "Nature's Basket", 'Grocery'),
  portal('godrej-natures', "Godrej Nature's Basket", 'Grocery'),
  portal('milkbasket', 'Milkbasket', 'Grocery'),
  portal('dailyninja', 'DailyNinja', 'Grocery'),
  portal('supr-daily', 'Supr Daily', 'Grocery'),
  portal('country-delight', 'Country Delight', 'Grocery'),
  portal('licious', 'Licious', 'Grocery'),
  portal('freshtohome', 'FreshToHome', 'Grocery'),
  portal('zappfresh', 'ZappFresh', 'Grocery'),
  portal('meatigo', 'Meatigo', 'Grocery'),

  // ===== TRAVEL - FLIGHTS =====
  portal('makemytrip', 'MakeMyTrip', 'Travel'),
  portal('cleartrip', 'Cleartrip', 'Travel'),
  portal('goibibo', 'Goibibo', 'Travel'),
  portal('yatra', 'Yatra', 'Travel'),
  portal('easemytrip', 'EaseMyTrip', 'Travel'),
  portal('ixigo', 'Ixigo', 'Travel'),
  portal('via', 'Via.com', 'Travel'),
  portal('happyeasygo', 'HappyEasyGo', 'Travel'),
  portal('paytm-travel', 'Paytm Travel', 'Travel'),
  portal('expedia', 'Expedia', 'Travel'),
  portal('booking', 'Booking.com', 'Travel'),
  portal('agoda', 'Agoda', 'Travel'),
  portal('skyscanner', 'Skyscanner', 'Travel'),
  portal('kayak', 'Kayak', 'Travel'),
  portal('google-flights', 'Google Flights', 'Travel'),
  portal('airbnb', 'Airbnb', 'Travel'),
  portal('tripadvisor', 'TripAdvisor', 'Travel'),
  portal('trivago', 'Trivago', 'Travel'),
  portal('irctc', 'IRCTC', 'Travel'),
  portal('confirmtkt', 'ConfirmTkt', 'Travel'),
  portal('railyatri', 'RailYatri', 'Travel'),
  portal('trainman', 'Trainman', 'Travel'),
  portal('redbus', 'redBus', 'Travel'),
  portal('abhibus', 'AbhiBus', 'Travel'),
  portal('paytm-bus', 'Paytm Bus', 'Travel'),
  portal('intrcity', 'IntrCity SmartBus', 'Travel'),
  portal('air-india', 'Air India', 'Airlines'),
  portal('indigo', 'IndiGo', 'Airlines'),
  portal('spicejet', 'SpiceJet', 'Airlines'),
  portal('vistara', 'Vistara', 'Airlines'),
  portal('goair', 'Go First', 'Airlines'),
  portal('akasa', 'Akasa Air', 'Airlines'),
  portal('airasia-india', 'AirAsia India', 'Airlines'),
  portal('emirates', 'Emirates', 'Airlines'),
  portal('singapore-airlines', 'Singapore Airlines', 'Airlines'),
  portal('qatar-airways', 'Qatar Airways', 'Airlines'),
  portal('etihad', 'Etihad Airways', 'Airlines'),
  portal('lufthansa', 'Lufthansa', 'Airlines'),
  portal('british-airways', 'British Airways', 'Airlines'),
  portal('thai-airways', 'Thai Airways', 'Airlines'),
  portal('cathay-pacific', 'Cathay Pacific', 'Airlines'),

  // ===== TRAVEL - HOTELS =====
  portal('oyo', 'OYO', 'Hotels'),
  portal('treebo', 'Treebo', 'Hotels'),
  portal('fabhotels', 'FabHotels', 'Hotels'),
  portal('zostel', 'Zostel', 'Hotels'),
  portal('hostelworld', 'Hostelworld', 'Hotels'),
  portal('taj-hotels', 'Taj Hotels', 'Hotels'),
  portal('itc-hotels', 'ITC Hotels', 'Hotels'),
  portal('oberoi', 'Oberoi Hotels', 'Hotels'),
  portal('leela', 'The Leela', 'Hotels'),
  portal('marriott', 'Marriott', 'Hotels'),
  portal('hilton', 'Hilton', 'Hotels'),
  portal('hyatt', 'Hyatt', 'Hotels'),
  portal('radisson', 'Radisson', 'Hotels'),
  portal('ihg', 'IHG', 'Hotels'),
  portal('accor', 'Accor', 'Hotels'),
  portal('lemon-tree', 'Lemon Tree', 'Hotels'),
  portal('ginger', 'Ginger Hotels', 'Hotels'),
  portal('club-mahindra', 'Club Mahindra', 'Hotels'),
  portal('sterling', 'Sterling Holidays', 'Hotels'),

  // ===== TRAVEL - EXPERIENCES =====
  portal('thrillophilia', 'Thrillophilia', 'Travel Experiences'),
  portal('viator', 'Viator', 'Travel Experiences'),
  portal('klook', 'Klook', 'Travel Experiences'),
  portal('getyourguide', 'GetYourGuide', 'Travel Experiences'),
  portal('headout', 'Headout', 'Travel Experiences'),
  portal('traveltrianle', 'TravelTriangle', 'Travel Experiences'),
  portal('holidify', 'Holidify', 'Travel Experiences'),
  portal('thomas-cook', 'Thomas Cook', 'Travel Experiences'),
  portal('cox-kings', 'Cox & Kings', 'Travel Experiences'),
  portal('sotc', 'SOTC', 'Travel Experiences'),
  portal('kesari', 'Kesari Tours', 'Travel Experiences'),
  portal('veena-world', 'Veena World', 'Travel Experiences'),

  // ===== CAB & TRANSPORT =====
  portal('uber', 'Uber', 'Cab & Transport'),
  portal('ola', 'Ola', 'Cab & Transport'),
  portal('rapido', 'Rapido', 'Cab & Transport'),
  portal('meru', 'Meru Cabs', 'Cab & Transport'),
  portal('bluesmart', 'BluSmart', 'Cab & Transport'),
  portal('namma-yatri', 'Namma Yatri', 'Cab & Transport'),
  portal('bounce', 'Bounce', 'Cab & Transport'),
  portal('vogo', 'Vogo', 'Cab & Transport'),
  portal('yulu', 'Yulu', 'Cab & Transport'),
  portal('zoomcar', 'Zoomcar', 'Car Rental'),
  portal('drivezy', 'Drivezy', 'Car Rental'),
  portal('revv', 'Revv', 'Car Rental'),
  portal('mylescars', 'Myles Cars', 'Car Rental'),
  portal('avis', 'Avis', 'Car Rental'),
  portal('hertz', 'Hertz', 'Car Rental'),
  portal('savaari', 'Savaari', 'Car Rental'),

  // ===== ENTERTAINMENT =====
  portal('bookmyshow', 'BookMyShow', 'Entertainment'),
  portal('paytm-movies', 'Paytm Movies', 'Entertainment'),
  portal('pvr', 'PVR Cinemas', 'Entertainment'),
  portal('inox', 'INOX', 'Entertainment'),
  portal('cinepolis', 'Cinepolis', 'Entertainment'),
  portal('carnival', 'Carnival Cinemas', 'Entertainment'),
  portal('netflix', 'Netflix', 'OTT Streaming'),
  portal('amazon-prime', 'Amazon Prime Video', 'OTT Streaming'),
  portal('hotstar', 'Disney+ Hotstar', 'OTT Streaming'),
  portal('sonyliv', 'SonyLIV', 'OTT Streaming'),
  portal('zee5', 'ZEE5', 'OTT Streaming'),
  portal('voot', 'Voot', 'OTT Streaming'),
  portal('jiocinema', 'JioCinema', 'OTT Streaming'),
  portal('mxplayer', 'MX Player', 'OTT Streaming'),
  portal('alt-balaji', 'ALTBalaji', 'OTT Streaming'),
  portal('eros-now', 'Eros Now', 'OTT Streaming'),
  portal('lionsgate', 'Lionsgate Play', 'OTT Streaming'),
  portal('discovery', 'Discovery+', 'OTT Streaming'),
  portal('apple-tv', 'Apple TV+', 'OTT Streaming'),
  portal('youtube-premium', 'YouTube Premium', 'OTT Streaming'),
  portal('spotify', 'Spotify', 'Music Streaming'),
  portal('jiosaavn', 'JioSaavn', 'Music Streaming'),
  portal('gaana', 'Gaana', 'Music Streaming'),
  portal('wynk', 'Wynk Music', 'Music Streaming'),
  portal('amazon-music', 'Amazon Music', 'Music Streaming'),
  portal('apple-music', 'Apple Music', 'Music Streaming'),
  portal('hungama', 'Hungama', 'Music Streaming'),

  // ===== GAMING =====
  portal('dream11', 'Dream11', 'Gaming'),
  portal('mpl', 'MPL', 'Gaming'),
  portal('winzo', 'WinZO', 'Gaming'),
  portal('rummycircle', 'RummyCircle', 'Gaming'),
  portal('pokerbaazi', 'PokerBaazi', 'Gaming'),
  portal('a23', 'A23 Rummy', 'Gaming'),
  portal('junglee-rummy', 'Junglee Rummy', 'Gaming'),
  portal('paytm-games', 'Paytm First Games', 'Gaming'),
  portal('my11circle', 'My11Circle', 'Gaming'),
  portal('fancode', 'FanCode', 'Gaming'),
  portal('playstation', 'PlayStation', 'Gaming'),
  portal('xbox', 'Xbox', 'Gaming'),
  portal('steam', 'Steam', 'Gaming'),
  portal('epicgames', 'Epic Games', 'Gaming'),

  // ===== ELECTRONICS & GADGETS =====
  portal('apple', 'Apple', 'Electronics'),
  portal('samsung', 'Samsung', 'Electronics'),
  portal('oneplus', 'OnePlus', 'Electronics'),
  portal('xiaomi', 'Xiaomi', 'Electronics'),
  portal('realme', 'Realme', 'Electronics'),
  portal('oppo', 'OPPO', 'Electronics'),
  portal('vivo', 'Vivo', 'Electronics'),
  portal('asus', 'ASUS', 'Electronics'),
  portal('dell', 'Dell', 'Electronics'),
  portal('hp', 'HP', 'Electronics'),
  portal('lenovo', 'Lenovo', 'Electronics'),
  portal('acer', 'Acer', 'Electronics'),
  portal('lg', 'LG', 'Electronics'),
  portal('sony', 'Sony', 'Electronics'),
  portal('panasonic', 'Panasonic', 'Electronics'),
  portal('philips', 'Philips', 'Electronics'),
  portal('boat', 'boAt', 'Electronics'),
  portal('noise', 'Noise', 'Electronics'),
  portal('fire-boltt', 'Fire-Boltt', 'Electronics'),
  portal('jabra', 'Jabra', 'Electronics'),
  portal('jbl', 'JBL', 'Electronics'),
  portal('bose', 'Bose', 'Electronics'),
  portal('sennheiser', 'Sennheiser', 'Electronics'),
  portal('marshall', 'Marshall', 'Electronics'),
  portal('harman-kardon', 'Harman Kardon', 'Electronics'),
  portal('gopro', 'GoPro', 'Electronics'),
  portal('dji', 'DJI', 'Electronics'),
  portal('canon', 'Canon', 'Electronics'),
  portal('nikon', 'Nikon', 'Electronics'),
  portal('fujifilm', 'Fujifilm', 'Electronics'),

  // ===== HEALTHCARE & PHARMACY =====
  portal('1mg', '1mg', 'Healthcare'),
  portal('pharmeasy', 'PharmEasy', 'Healthcare'),
  portal('netmeds', 'Netmeds', 'Healthcare'),
  portal('apollo-pharmacy', 'Apollo Pharmacy', 'Healthcare'),
  portal('medlife', 'Medlife', 'Healthcare'),
  portal('healthkart', 'HealthKart', 'Healthcare'),
  portal('wellness-forever', 'Wellness Forever', 'Healthcare'),
  portal('medplus', 'MedPlus', 'Healthcare'),
  portal('practo', 'Practo', 'Healthcare'),
  portal('apollo247', 'Apollo 24|7', 'Healthcare'),
  portal('tata-1mg', 'Tata 1mg', 'Healthcare'),
  portal('cult-fit', 'cult.fit', 'Fitness'),
  portal('fitternity', 'Fitternity', 'Fitness'),
  portal('gold-gym', "Gold's Gym", 'Fitness'),
  portal('anytime-fitness', 'Anytime Fitness', 'Fitness'),
  portal('fitpass', 'Fitpass', 'Fitness'),
  portal('cure-fit', 'Cure.fit', 'Fitness'),
  portal('healthify', 'HealthifyMe', 'Fitness'),

  // ===== HOME & FURNITURE =====
  portal('ikea', 'IKEA', 'Home & Furniture'),
  portal('pepperfry', 'Pepperfry', 'Home & Furniture'),
  portal('urban-ladder', 'Urban Ladder', 'Home & Furniture'),
  portal('hometown', 'HomeTown', 'Home & Furniture'),
  portal('godrej-interio', 'Godrej Interio', 'Home & Furniture'),
  portal('wooden-street', 'Wooden Street', 'Home & Furniture'),
  portal('wakefit', 'Wakefit', 'Home & Furniture'),
  portal('sleepyhead', 'Sleepyhead', 'Home & Furniture'),
  portal('duroflex', 'Duroflex', 'Home & Furniture'),
  portal('kurlon', 'Kurlon', 'Home & Furniture'),
  portal('nilkamal', 'Nilkamal', 'Home & Furniture'),
  portal('home-centre', 'Home Centre', 'Home & Furniture'),
  portal('fabfurnish', 'FabFurnish', 'Home & Furniture'),
  portal('houzz', 'Houzz', 'Home & Furniture'),
  portal('livspace', 'Livspace', 'Home & Furniture'),
  portal('asian-paints', 'Asian Paints', 'Home & Furniture'),
  portal('berger', 'Berger Paints', 'Home & Furniture'),
  portal('dulux', 'Dulux', 'Home & Furniture'),

  // ===== BABY & KIDS =====
  portal('firstcry', 'FirstCry', 'Baby & Kids'),
  portal('hopscotch', 'Hopscotch', 'Baby & Kids'),
  portal('babyoye', 'Babyoye', 'Baby & Kids'),
  portal('mamy-poko', 'MamyPoko', 'Baby & Kids'),
  portal('pampers', 'Pampers', 'Baby & Kids'),
  portal('huggies', 'Huggies', 'Baby & Kids'),
  portal('johnson-baby', "Johnson's Baby", 'Baby & Kids'),
  portal('mothercare', 'Mothercare', 'Baby & Kids'),
  portal('hamleys', 'Hamleys', 'Baby & Kids'),
  portal('toy-kingdom', 'Toy Kingdom', 'Baby & Kids'),

  // ===== PET SUPPLIES =====
  portal('supertails', 'Supertails', 'Pet Supplies'),
  portal('heads-up-tails', 'Heads Up For Tails', 'Pet Supplies'),
  portal('petsy', 'Petsy', 'Pet Supplies'),
  portal('marshalls', "Marshall's", 'Pet Supplies'),
  portal('petsworld', 'PetsWorld', 'Pet Supplies'),
  portal('zigly', 'Zigly', 'Pet Supplies'),

  // ===== EDUCATION =====
  portal('byjus', "BYJU'S", 'Education'),
  portal('unacademy', 'Unacademy', 'Education'),
  portal('vedantu', 'Vedantu', 'Education'),
  portal('toppr', 'Toppr', 'Education'),
  portal('meritnation', 'Meritnation', 'Education'),
  portal('doubtnut', 'Doubtnut', 'Education'),
  portal('physics-wallah', 'Physics Wallah', 'Education'),
  portal('udemy', 'Udemy', 'Education'),
  portal('coursera', 'Coursera', 'Education'),
  portal('edx', 'edX', 'Education'),
  portal('skillshare', 'Skillshare', 'Education'),
  portal('linkedin-learning', 'LinkedIn Learning', 'Education'),
  portal('simplilearn', 'Simplilearn', 'Education'),
  portal('upgrad', 'upGrad', 'Education'),
  portal('greatlearning', 'Great Learning', 'Education'),
  portal('scaler', 'Scaler', 'Education'),
  portal('coding-ninjas', 'Coding Ninjas', 'Education'),
  portal('geeksforgeeks', 'GeeksforGeeks', 'Education'),
  portal('leetcode', 'LeetCode', 'Education'),
  portal('hackerrank', 'HackerRank', 'Education'),
  portal('whitehat-jr', 'WhiteHat Jr', 'Education'),
  portal('cuemath', 'Cuemath', 'Education'),
  portal('extramarks', 'Extramarks', 'Education'),
  portal('allen', 'Allen Career', 'Education'),
  portal('aakash', 'Aakash Institute', 'Education'),
  portal('fiitjee', 'FIITJEE', 'Education'),
  portal('resonance', 'Resonance', 'Education'),

  // ===== FINANCE & PAYMENTS =====
  portal('paytm', 'Paytm', 'Finance'),
  portal('phonepe', 'PhonePe', 'Finance'),
  portal('gpay', 'Google Pay', 'Finance'),
  portal('amazon-pay', 'Amazon Pay', 'Finance'),
  portal('freecharge', 'FreeCharge', 'Finance'),
  portal('mobikwik', 'MobiKwik', 'Finance'),
  portal('bhim', 'BHIM', 'Finance'),
  portal('cred', 'CRED', 'Finance'),
  portal('slice', 'Slice', 'Finance'),
  portal('uni', 'Uni Cards', 'Finance'),
  portal('onecared', 'OneCard', 'Finance'),
  portal('jupiter', 'Jupiter', 'Finance'),
  portal('fi', 'Fi Money', 'Finance'),
  portal('niyo', 'Niyo', 'Finance'),
  portal('razorpay', 'RazorpayX', 'Finance'),
  portal('groww', 'Groww', 'Finance'),
  portal('zerodha', 'Zerodha', 'Finance'),
  portal('upstox', 'Upstox', 'Finance'),
  portal('angelone', 'Angel One', 'Finance'),
  portal('5paisa', '5Paisa', 'Finance'),
  portal('paytm-money', 'Paytm Money', 'Finance'),
  portal('kuvera', 'Kuvera', 'Finance'),
  portal('etmoney', 'ET Money', 'Finance'),
  portal('coin-dcx', 'CoinDCX', 'Finance'),
  portal('wazirx', 'WazirX', 'Finance'),
  portal('coinswitch', 'CoinSwitch', 'Finance'),
  portal('policybazaar', 'PolicyBazaar', 'Insurance'),
  portal('acko', 'Acko', 'Insurance'),
  portal('digit', 'Digit Insurance', 'Insurance'),
  portal('turtlemint', 'Turtlemint', 'Insurance'),
  portal('coverfox', 'Coverfox', 'Insurance'),
  portal('paytm-insurance', 'Paytm Insurance', 'Insurance'),
  portal('bharti-axa', 'Bharti AXA', 'Insurance'),
  portal('hdfc-ergo', 'HDFC ERGO', 'Insurance'),
  portal('icici-lombard', 'ICICI Lombard', 'Insurance'),
  portal('bajaj-allianz', 'Bajaj Allianz', 'Insurance'),

  // ===== LOANS & LENDING =====
  portal('bajaj-finserv', 'Bajaj Finserv', 'Loans'),
  portal('hdfc-loans', 'HDFC Loans', 'Loans'),
  portal('tata-capital', 'Tata Capital', 'Loans'),
  portal('fullerton', 'Fullerton India', 'Loans'),
  portal('moneyview', 'MoneyView', 'Loans'),
  portal('cashbean', 'CashBean', 'Loans'),
  portal('dhani', 'Dhani', 'Loans'),
  portal('stashfin', 'Stashfin', 'Loans'),
  portal('navi', 'Navi', 'Loans'),
  portal('kreditbee', 'KreditBee', 'Loans'),
  portal('cashe', 'CASHe', 'Loans'),
  portal('earlysalary', 'EarlySalary', 'Loans'),
  portal('lazypay', 'LazyPay', 'Loans'),
  portal('simpl', 'Simpl', 'Loans'),
  portal('zestmoney', 'ZestMoney', 'Loans'),

  // ===== TELECOM =====
  portal('jio', 'Jio', 'Telecom'),
  portal('airtel', 'Airtel', 'Telecom'),
  portal('vi', 'Vi', 'Telecom'),
  portal('bsnl', 'BSNL', 'Telecom'),
  portal('mtnl', 'MTNL', 'Telecom'),
  portal('airtel-xstream', 'Airtel Xstream', 'Telecom'),
  portal('jio-fiber', 'Jio Fiber', 'Telecom'),
  portal('act-fibernet', 'ACT Fibernet', 'Telecom'),
  portal('hathway', 'Hathway', 'Telecom'),
  portal('tata-sky', 'Tata Play', 'Telecom'),
  portal('dish-tv', 'Dish TV', 'Telecom'),
  portal('d2h', 'd2h', 'Telecom'),
  portal('sun-direct', 'Sun Direct', 'Telecom'),

  // ===== REAL ESTATE =====
  portal('99acres', '99acres', 'Real Estate'),
  portal('magicbricks', 'MagicBricks', 'Real Estate'),
  portal('housing', 'Housing.com', 'Real Estate'),
  portal('nobroker', 'NoBroker', 'Real Estate'),
  portal('square-yards', 'Square Yards', 'Real Estate'),
  portal('commonfloor', 'CommonFloor', 'Real Estate'),
  portal('makaan', 'Makaan', 'Real Estate'),
  portal('proptiger', 'PropTiger', 'Real Estate'),
  portal('nestaway', 'NestAway', 'Real Estate'),
  portal('oyo-life', 'OYO LIFE', 'Real Estate'),
  portal('zolo', 'Zolo', 'Real Estate'),
  portal('stanza', 'Stanza Living', 'Real Estate'),
  portal('colive', 'Colive', 'Real Estate'),

  // ===== JOB PORTALS =====
  portal('naukri', 'Naukri', 'Jobs'),
  portal('linkedin', 'LinkedIn', 'Jobs'),
  portal('indeed', 'Indeed', 'Jobs'),
  portal('monster', 'Monster', 'Jobs'),
  portal('shine', 'Shine', 'Jobs'),
  portal('timesjobs', 'TimesJobs', 'Jobs'),
  portal('glassdoor', 'Glassdoor', 'Jobs'),
  portal('instahyre', 'Instahyre', 'Jobs'),
  portal('hirist', 'Hirist', 'Jobs'),
  portal('cutshort', 'CutShort', 'Jobs'),
  portal('angel', 'AngelList', 'Jobs'),
  portal('internshala', 'Internshala', 'Jobs'),
  portal('freshersworld', 'Freshersworld', 'Jobs'),
  portal('apna', 'Apna', 'Jobs'),
  portal('workex', 'WorkEx', 'Jobs'),

  // ===== MATRIMONY =====
  portal('shaadi', 'Shaadi.com', 'Matrimony'),
  portal('bharatmatrimony', 'BharatMatrimony', 'Matrimony'),
  portal('jeevansathi', 'Jeevansathi', 'Matrimony'),
  portal('tamilmatrimony', 'TamilMatrimony', 'Matrimony'),
  portal('telugumatrimony', 'TeluguMatrimony', 'Matrimony'),
  portal('elitematrimony', 'Elite Matrimony', 'Matrimony'),

  // ===== DATING =====
  portal('tinder', 'Tinder', 'Dating'),
  portal('bumble', 'Bumble', 'Dating'),
  portal('hinge', 'Hinge', 'Dating'),
  portal('happn', 'Happn', 'Dating'),
  portal('trulymadly', 'TrulyMadly', 'Dating'),
  portal('aisle', 'Aisle', 'Dating'),
  portal('woo', 'Woo', 'Dating'),

  // ===== NEWS & MEDIA =====
  portal('times-of-india', 'Times of India', 'News'),
  portal('hindustan-times', 'Hindustan Times', 'News'),
  portal('indian-express', 'Indian Express', 'News'),
  portal('ndtv', 'NDTV', 'News'),
  portal('news18', 'News18', 'News'),
  portal('india-today', 'India Today', 'News'),
  portal('economic-times', 'Economic Times', 'News'),
  portal('mint', 'Mint', 'News'),
  portal('business-standard', 'Business Standard', 'News'),
  portal('moneycontrol', 'Moneycontrol', 'News'),
  portal('dailyhunt', 'DailyHunt', 'News'),
  portal('inshorts', 'Inshorts', 'News'),
  portal('newspoint', 'NewsPoint', 'News'),

  // ===== AUTOMOBILE =====
  portal('carwale', 'CarWale', 'Automobile'),
  portal('cardekho', 'CarDekho', 'Automobile'),
  portal('bikewale', 'BikeWale', 'Automobile'),
  portal('bikedekho', 'BikeDekho', 'Automobile'),
  portal('cars24', 'Cars24', 'Automobile'),
  portal('spinny', 'Spinny', 'Automobile'),
  portal('olx-autos', 'OLX Autos', 'Automobile'),
  portal('droom', 'Droom', 'Automobile'),
  portal('truebil', 'Truebil', 'Automobile'),
  portal('carsome', 'Carsome', 'Automobile'),
  portal('park-plus', 'Park+', 'Automobile'),
  portal('fixcraft', 'Fixcraft', 'Automobile'),
  portal('gomechanic', 'GoMechanic', 'Automobile'),
  portal('pitstop', 'Pitstop', 'Automobile'),
  portal('tyremarket', 'Tyre Market', 'Automobile'),
  portal('ceat', 'CEAT Tyres', 'Automobile'),
  portal('mrf', 'MRF', 'Automobile'),
  portal('apollo-tyres', 'Apollo Tyres', 'Automobile'),

  // ===== FUEL =====
  portal('indian-oil', 'Indian Oil', 'Fuel'),
  portal('bharat-petroleum', 'BPCL', 'Fuel'),
  portal('hp', 'HP Petrol', 'Fuel'),
  portal('reliance-petrol', 'Reliance Petrol', 'Fuel'),
  portal('shell', 'Shell', 'Fuel'),

  // ===== GIFTING =====
  portal('ferns-n-petals', 'Ferns N Petals', 'Gifting'),
  portal('igp', 'IGP', 'Gifting'),
  portal('floweraura', 'FlowerAura', 'Gifting'),
  portal('winni', 'Winni', 'Gifting'),
  portal('archiesonline', 'Archies', 'Gifting'),
  portal('hallmark', 'Hallmark', 'Gifting'),
  portal('giftease', 'Giftease', 'Gifting'),
  portal('bigsmall', 'Bigsmall', 'Gifting'),
  portal('confetti-gifts', 'Confetti', 'Gifting'),

  // ===== JEWELLERY =====
  portal('tanishq', 'Tanishq', 'Jewellery'),
  portal('caratlane', 'CaratLane', 'Jewellery'),
  portal('bluestone', 'BlueStone', 'Jewellery'),
  portal('malabar-gold', 'Malabar Gold', 'Jewellery'),
  portal('kalyan', 'Kalyan Jewellers', 'Jewellery'),
  portal('pc-jeweller', 'PC Jeweller', 'Jewellery'),
  portal('senco', 'Senco Gold', 'Jewellery'),
  portal('joyalukkas', 'Joyalukkas', 'Jewellery'),
  portal('giva', 'GIVA', 'Jewellery'),
  portal('melorra', 'Melorra', 'Jewellery'),
  portal('candere', 'Candere', 'Jewellery'),
  portal('qudera', 'Qudera', 'Jewellery'),
  portal('titan-jewellery', 'Titan Jewellery', 'Jewellery'),

  // ===== WATCHES =====
  portal('titan', 'Titan', 'Watches'),
  portal('fastrack', 'Fastrack', 'Watches'),
  portal('sonata', 'Sonata', 'Watches'),
  portal('timex', 'Timex', 'Watches'),
  portal('casio', 'Casio', 'Watches'),
  portal('fossil', 'Fossil', 'Watches'),
  portal('guess', 'Guess', 'Watches'),
  portal('michael-kors', 'Michael Kors', 'Watches'),
  portal('daniel-wellington', 'Daniel Wellington', 'Watches'),
  portal('tissot', 'Tissot', 'Watches'),

  // ===== SPORTS & OUTDOOR =====
  portal('decathlon', 'Decathlon', 'Sports'),
  portal('sports365', 'Sports365', 'Sports'),
  portal('yonex', 'Yonex', 'Sports'),
  portal('nivia', 'Nivia', 'Sports'),
  portal('cosco', 'Cosco', 'Sports'),
  portal('sg', 'SG Cricket', 'Sports'),
  portal('mrf-bats', 'MRF', 'Sports'),
  portal('ss-cricket', 'SS Cricket', 'Sports'),
  portal('kookaburra', 'Kookaburra', 'Sports'),
  portal('gray-nicolls', 'Gray-Nicolls', 'Sports'),

  // ===== BOOKS & STATIONERY =====
  portal('amazon-books', 'Amazon Books', 'Books'),
  portal('flipkart-books', 'Flipkart Books', 'Books'),
  portal('crossword', 'Crossword', 'Books'),
  portal('landmark', 'Landmark', 'Books'),
  portal('bookswagon', 'BooksWagon', 'Books'),
  portal('sapnaonline', 'Sapna Online', 'Books'),
  portal('instamojo', 'Instamojo Books', 'Books'),
  portal('kindle', 'Kindle', 'Books'),
  portal('audible', 'Audible', 'Books'),
  portal('storytel', 'Storytel', 'Books'),
  portal('google-books', 'Google Books', 'Books'),
  portal('classmate', 'Classmate', 'Stationery'),
  portal('camlin', 'Camlin', 'Stationery'),
  portal('navneet', 'Navneet', 'Stationery'),
  portal('doms', 'Doms', 'Stationery'),

  // ===== DIGITAL SERVICES =====
  portal('google-one', 'Google One', 'Digital Services'),
  portal('icloud', 'iCloud', 'Digital Services'),
  portal('dropbox', 'Dropbox', 'Digital Services'),
  portal('microsoft-365', 'Microsoft 365', 'Digital Services'),
  portal('adobe-cc', 'Adobe Creative Cloud', 'Digital Services'),
  portal('canva-pro', 'Canva Pro', 'Digital Services'),
  portal('notion', 'Notion', 'Digital Services'),
  portal('slack', 'Slack', 'Digital Services'),
  portal('zoom', 'Zoom', 'Digital Services'),
  portal('google-workspace', 'Google Workspace', 'Digital Services'),
  portal('github', 'GitHub', 'Digital Services'),
  portal('figma', 'Figma', 'Digital Services'),
  portal('grammarly', 'Grammarly', 'Digital Services'),
  portal('chatgpt', 'ChatGPT Plus', 'Digital Services'),
  portal('claude', 'Claude Pro', 'Digital Services'),
  portal('midjourney', 'Midjourney', 'Digital Services'),

  // ===== SECOND HAND / CLASSIFIEDS =====
  portal('olx', 'OLX', 'Classifieds'),
  portal('quikr', 'Quikr', 'Classifieds'),
  portal('cashify', 'Cashify', 'Classifieds'),
  portal('budli', 'Budli', 'Classifieds'),
  portal('instacash', 'InstaCash', 'Classifieds'),
  portal('yaantra', 'Yaantra', 'Classifieds'),
  portal('2gud', '2GUD', 'Classifieds'),
  portal('togofogo', 'Togofogo', 'Classifieds'),

  // ===== EVENTS & TICKETS =====
  portal('insider', 'Insider.in', 'Events'),
  portal('skillbox', 'Skillbox', 'Events'),
  portal('eventbrite', 'Eventbrite', 'Events'),
  portal('explara', 'Explara', 'Events'),
  portal('town-script', 'Townscript', 'Events'),
  portal('meraevents', 'MeraEvents', 'Events'),
  portal('allevents', 'AllEvents', 'Events'),
  portal('paytm-insider', 'Paytm Insider', 'Events'),

  // ===== HOME SERVICES =====
  portal('urbancompany', 'Urban Company', 'Home Services'),
  portal('housejoy', 'Housejoy', 'Home Services'),
  portal('zimmber', 'Zimmber', 'Home Services'),
  portal('taskrabbit', 'TaskRabbit', 'Home Services'),
  portal('bro4u', 'Bro4u', 'Home Services'),
  portal('local-oye', 'LocalOye', 'Home Services'),
  portal('justdial', 'JustDial', 'Home Services'),
  portal('sulekha', 'Sulekha', 'Home Services'),

  // ===== LAUNDRY & DRY CLEANING =====
  portal('laundrymate', 'LaundryMate', 'Laundry'),
  portal('uclean', 'UClean', 'Laundry'),
  portal('washho', 'Washho', 'Laundry'),
  portal('pressto', 'Pressto', 'Laundry'),
  portal('tumbledry', 'Tumbledry', 'Laundry'),
  portal('laundrokart', 'Laundrokart', 'Laundry'),

  // ===== SALON & SPA =====
  portal('urbancompany-salon', 'Urban Company Salon', 'Salon & Spa'),
  portal('naturals', 'Naturals Salon', 'Salon & Spa'),
  portal('lakme-salon', 'Lakme Salon', 'Salon & Spa'),
  portal('jawed-habib', 'Jawed Habib', 'Salon & Spa'),
  portal('vlcc', 'VLCC', 'Salon & Spa'),
  portal('kaya', 'Kaya Clinic', 'Salon & Spa'),
  portal('oliva', 'Oliva Clinic', 'Salon & Spa'),
  portal('bodycraft', 'Bodycraft', 'Salon & Spa'),
  portal('o2-spa', 'O2 Spa', 'Salon & Spa'),
  portal('four-fountains', 'Four Fountains Spa', 'Salon & Spa'),

  // ===== PRINTING & PERSONALIZATION =====
  portal('vistaprint', 'Vistaprint', 'Printing'),
  portal('printo', 'Printo', 'Printing'),
  portal('printland', 'Printland', 'Printing'),
  portal('zoomin', 'Zoomin', 'Printing'),
  portal('canvera', 'Canvera', 'Printing'),
  portal('printbindaas', 'Print Bindaas', 'Printing'),
  portal('printvenue', 'PrintVenue', 'Printing'),

  // ===== CLOUD & HOSTING =====
  portal('aws', 'AWS', 'Cloud'),
  portal('azure', 'Microsoft Azure', 'Cloud'),
  portal('gcp', 'Google Cloud', 'Cloud'),
  portal('digitalocean', 'DigitalOcean', 'Cloud'),
  portal('godaddy', 'GoDaddy', 'Cloud'),
  portal('hostinger', 'Hostinger', 'Cloud'),
  portal('bluehost', 'Bluehost', 'Cloud'),
  portal('hostgator', 'HostGator', 'Cloud'),
  portal('bigrock', 'BigRock', 'Cloud'),
  portal('namecheap', 'Namecheap', 'Cloud'),

  // ===== LEGAL & COMPLIANCE =====
  portal('cleartax', 'ClearTax', 'Legal'),
  portal('taxbuddy', 'TaxBuddy', 'Legal'),
  portal('vakilsearch', 'Vakilsearch', 'Legal'),
  portal('legalzoom', 'LegalZoom', 'Legal'),
  portal('indiafilings', 'IndiaFilings', 'Legal'),
  portal('quickcompany', 'QuickCompany', 'Legal'),
  portal('corpbiz', 'Corpbiz', 'Legal'),
  portal('myonlineca', 'MyOnlineCA', 'Legal'),
];

export function Search() {
  const navigate = useNavigate();
  const { location } = useLocation();
  const { results, isLoading, search, clearResults } = useSearch();
  const [searchQuery, setSearchQuery] = useState('');

  // Filter online portals based on search query
  const matchingOnlinePortals = useMemo(() => {
    if (searchQuery.length < 2) return [];
    const query = searchQuery.toLowerCase();
    return ONLINE_PORTALS.filter(
      (portal) =>
        portal.name.toLowerCase().includes(query) ||
        portal.category?.toLowerCase().includes(query)
    );
  }, [searchQuery]);

  // Show popular portals when no search query
  const popularPortals = useMemo(() => {
    return ONLINE_PORTALS.slice(0, 8); // Show first 8 popular portals
  }, []);

  useEffect(() => {
    const timeoutId = setTimeout(() => {
      if (searchQuery.length >= 2) {
        search(searchQuery, location?.latitude, location?.longitude);
      } else {
        clearResults();
      }
    }, 300);

    return () => clearTimeout(timeoutId);
  }, [searchQuery, location, search, clearResults]);

  const handleMerchantSelect = (merchant: Merchant) => {
    const params = new URLSearchParams({
      name: merchant.name,
      placeId: merchant.id,
    });
    if (merchant.category) params.append('category', merchant.category);
    if (merchant.locations?.[0]?.address) params.append('address', merchant.locations[0].address);
    // Mark as online portal for recommendation engine
    if (merchant.id.startsWith('online-')) params.append('is_online', 'true');
    navigate(`/recommendation?${params.toString()}`);
  };

  return (
    <div className="min-h-screen bg-white dark:bg-gray-900">
      {/* Header */}
      <div className="sticky top-0 bg-white dark:bg-gray-900 border-b border-gray-100 dark:border-gray-800 z-10">
        <div className="flex items-center gap-3 p-4">
          <button
            onClick={() => navigate(-1)}
            className="p-2 hover:bg-gray-100 dark:hover:bg-gray-800 rounded-lg"
          >
            <ArrowLeft className="w-5 h-5" />
          </button>
          <div className="flex-1">
            <SearchBar
              value={searchQuery}
              onChange={setSearchQuery}
              autoFocus
              placeholder="Search restaurant, store, or place..."
            />
          </div>
        </div>
      </div>

      {/* Content */}
      <div className="p-4">
        {searchQuery.length < 2 ? (
          <div className="space-y-6">
            {/* Popular Online Portals */}
            <div>
              <div className="flex items-center gap-2 mb-3">
                <Globe className="w-4 h-4 text-primary-600" />
                <h3 className="text-sm font-medium text-gray-700 dark:text-gray-300">
                  Popular Online Portals
                </h3>
              </div>
              <div className="grid grid-cols-4 gap-3">
                {popularPortals.map((portal) => (
                  <button
                    key={portal.id}
                    onClick={() => handleMerchantSelect(portal)}
                    className="flex flex-col items-center p-3 bg-gray-50 dark:bg-gray-800 rounded-xl hover:bg-primary-50 dark:hover:bg-primary-900/20 transition-colors"
                  >
                    <div className="w-10 h-10 bg-primary-100 dark:bg-primary-900/30 rounded-full flex items-center justify-center mb-2">
                      <span className="text-lg font-semibold text-primary-600">
                        {portal.name[0]}
                      </span>
                    </div>
                    <span className="text-xs text-gray-700 dark:text-gray-300 text-center truncate w-full">
                      {portal.name}
                    </span>
                  </button>
                ))}
              </div>
            </div>
            <div className="text-center py-4 text-gray-500 dark:text-gray-400">
              <p>Or type to search for stores near you</p>
            </div>
          </div>
        ) : (
          <>
            {/* Online Portals matching search */}
            {matchingOnlinePortals.length > 0 && (
              <div className="mb-6">
                <div className="flex items-center gap-2 mb-3">
                  <Globe className="w-4 h-4 text-primary-600" />
                  <h3 className="text-sm font-medium text-gray-700 dark:text-gray-300">
                    Online Portals
                  </h3>
                </div>
                <div className="space-y-2">
                  {matchingOnlinePortals.map((portal) => (
                    <button
                      key={portal.id}
                      onClick={() => handleMerchantSelect(portal)}
                      className="w-full flex items-center gap-3 p-3 bg-gray-50 dark:bg-gray-800 rounded-xl hover:bg-primary-50 dark:hover:bg-primary-900/20 transition-colors text-left"
                    >
                      <div className="w-10 h-10 bg-primary-100 dark:bg-primary-900/30 rounded-full flex items-center justify-center flex-shrink-0">
                        <span className="text-lg font-semibold text-primary-600">
                          {portal.name[0]}
                        </span>
                      </div>
                      <div>
                        <div className="font-medium text-gray-900 dark:text-white">
                          {portal.name}
                        </div>
                        <div className="text-xs text-gray-500 dark:text-gray-400">
                          {portal.category}
                        </div>
                      </div>
                    </button>
                  ))}
                </div>
              </div>
            )}

            {/* Loading indicator for places search */}
            {isLoading && (
              <div className="mb-4">
                <Loading text="Searching nearby places..." />
              </div>
            )}

            {/* Near You section */}
            {!isLoading && results.some((m) => (m.locations || []).some((l) => l.distance_km !== undefined)) && (
              <PlacesList
                merchants={results.filter((m) =>
                  (m.locations || []).some((l) => l.distance_km !== undefined)
                )}
                onSelect={handleMerchantSelect}
                title="Near You"
              />
            )}

            {/* All Locations section */}
            {!isLoading && results.some((m) => (m.locations || []).length === 0 || m.is_chain) && (
              <div className="mt-6">
                <PlacesList
                  merchants={results.filter(
                    (m) => (m.locations || []).length === 0 || m.is_chain
                  )}
                  onSelect={handleMerchantSelect}
                  title="All Locations"
                />
              </div>
            )}

            {/* No results message */}
            {!isLoading && matchingOnlinePortals.length === 0 && (!Array.isArray(results) || results.length === 0) && (
              <div className="text-center py-12 text-gray-500 dark:text-gray-400">
                <p>No results found for "{searchQuery}"</p>
              </div>
            )}
          </>
        )}
      </div>
    </div>
  );
}
