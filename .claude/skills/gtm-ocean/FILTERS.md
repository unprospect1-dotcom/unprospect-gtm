# Ocean.io — Catálogo completo de filtros y valores

> Extraído de app.ocean.io/docs + `/v2/data-fields` en vivo (GRATIS) 2026-07-13.
> Costos: 1 crédito/resultado de búsqueda + 1/email revelado. Preview (conteo) NO disponible
> en plan v3 self-serve (enterprise only) — por eso el sondeo barato es `size` mínimo.
> GRATIS: `/v2/credits/balance`, `/v2/warmup/companies`, `/v2/data-fields`, autocompletes.

## Cuándo usar qué filtro (playbook)

| Objetivo | Filtro | Nota |
|---|---|---|
| Lookalikes (SU superpoder) | `companiesFilters.lookalikeDomains` + `companyMatchingMode: precise|broad` | precise=semántica de producto; broad=misma industria. Warmup de seeds GRATIS antes. |
| Lookalike de PERSONAS | `peopleFilters.lookalikeLinkedinHandles` | Único en el stack. |
| Empresas por tamaño de UN DEPTO | `departmentSizes: [{department: "Sales", from, to}]` | 24 deptos abajo. Igual que AI Ark metric.employee. |
| Depto creciendo | `departmentGrowth` (as % o absoluto, 3/6/12 meses) | Señal de inversión en el área. |
| Tamaño LinkedIn vs Ocean | `employeeCountLinkedin` y `employeeCountOcean` (from/to) | DOS conteos separados — mismo tema que AI Ark staff.total vs range. |
| Industria | `industries.industries` (taxonomía propia, 46 categorías abajo) o `linkedinIndustries` (248) | Dos taxonomías independientes = dos lentes. |
| Keywords del sitio | `keywords: {anyOf/allOf/noneOf, minRelevance: A/B/C}` | Con score de relevancia — mejor que substring ciego. |
| Títulos de persona | `peopleFilters.jobTitleKeywords: {anyOf/allOf/noneOf}` | + `allJobDescriptions`/`currentJobDescription`/`profileDescription` para texto libre. |
| Cambio de puesto (timing) | `changedPositionAfter/Before` (YYYY-MM-DD) | Señal de intención clásica. |
| Geografía | `primaryLocations.includeCountries` — códigos ISO alpha-2 ("mx") | NO nombres. Regiones/estados via data-fields (regions.mx). |
| Tech stack | `technologies.apps/categories` (6,451 apps — consultar data-fields) | |
| Calidad de dato | `fieldsExist/fieldsNotExist` | ej. exigir que exista `departmentSizes` antes de filtrar por él. |
| Excluir conocidos | `excludeDomains` / `excludePeopleIds` / `excludeLinkedinHandles` | Dedupe contra Supabase antes de pagar. |

Sintaxis: `{size, searchAfter, companiesFilters: {...}, peopleFilters: {...}}`. Auth: header `x-api-token`.
En people search, `companiesFilters` anida igual (personas DE esas empresas). Otros filtros de empresa:
`ecommerce` (bool), `yearFounded`, `countriesCount`, `locationsCount`, `mobileAppsFilter`,
`fundingRound {raised, types: [Seed, Series A, ...]}`, `webTraffic {visits, views}`, `socialMedias`,
`headcountGrowth`, `updatedWithinMonths`. De persona: `connections`, `followers` (from/to).

## companySizes (12)

- `0-1`
- `2-10`
- `11-50`
- `51-200`
- `201-500`
- `501-1000`
- `1001-5000`
- `5001-10000`
- `10001-50000`
- `50001-100000`
- `100001-500000`
- `500000+`

## revenues (7)

- `0-1M`
- `1-10M`
- `10-50M`
- `50-100M`
- `100-500M`
- `500-1000M`
- `>1000M`

## seniorities de personas (10)

- `Owner`
- `Founder`
- `Board Member`
- `C-Level`
- `Partner`
- `VP`
- `Head`
- `Director`
- `Manager`
- `Other`

## departments (24 — para `departmentSizes`, `departmentGrowth` y `peopleFilters.departments`)

Asignados por función, no por seniority: un VP of Sales cae en "Sales", un CTO en "Engineering",
CMO en "Marketing and Advertising", CFO en "Accounting and Finance". "Management" es solo CEO/COO/GM.

- `Accounting and Finance`
- `Board`
- `Business Support`
- `Customer Relations`
- `Design`
- `Editorial Personnel`
- `Engineering`
- `Founder/Owner`
- `Healthcare`
- `HR`
- `Legal`
- `Management`
- `Manufacturing`
- `Marketing and Advertising`
- `Operations`
- `PR and Communications`
- `Procurement`
- `Product`
- `Quality Control`
- `R&D`
- `Sales`
- `Security`
- `Supply Chain`
- `Other`

## Taxonomía propia de industrias (46 categorías — `industryCategories` / `industries.industries`)

**Administrative Services**: Call Center, Collection Agency, Courier Service, Debt Collections, Delivery, Document Preparation, Extermination Service, Facilities Support Services, Housekeeping Service, Office Administration, Packaging Services, Physical Security, Staffing Agency, Trade Shows, Virtual Workforce
**Advertising**: Ad Network, Advertising, Advertising Platforms, Affiliate Marketing, Mobile Advertising, Outdoor Advertising, SEM, Social Media Advertising, Video Advertising
**Agriculture and Farming**: Agriculture, AgTech, Animal Feed, Aquaculture, Farming, Forestry, Horticulture, Livestock
**Apps**: Apps, Enterprise Applications, Mobile Apps, Web Apps
**Artificial Intelligence**: Artificial Intelligence, Intelligent Systems, Machine Learning, Natural Language Processing, Predictive Analytics
**Biotechnology**: Bioinformatics, Biometrics, Biopharma, Biotechnology, Genetics, Life Science, Neuroscience
**Clothing and Apparel**: Fashion, Laundry and Dry-cleaning, Lingerie, Shoes
**Commerce and Shopping**: Auctions, B2B, B2C, Commercial, Consumer Reviews, Consumer, Coupons, E-Commerce Platforms, E-Commerce, Gift Card, Gift, Handmade, Local Business, Local, Marketplace, Point of Sale, Price Comparison, Rental, Retail Technology, Retail, Sharing Economy, Shopping Mall, Shopping, Sporting Goods, Subscription Service, Wholesale
**Community and Lifestyle**: Adult, Association, Baby, Cannabis, Charity, Children, Communities, Dating, Elderly, Family, Homeless Shelter, Humanitarian, Leisure, Lifestyle, Men's, Non Profit, Parenting, Pet, Professional Networking, Religion, Retirement, Social Entrepreneurship, Social Impact, Social, Underserved Children, Wedding, Women's, Young Adults
**Consumer Electronics**: Computer, Consumer Electronics, Drones, Electronics, Mobile Devices, Smart Home, Wearables
**Consumer Goods**: Beauty, Comics, Consumer Goods, Cosmetics, Drones, Eyewear, Fast-Moving Consumer Goods, Flowers, Furniture, Jewelry, Lingerie, Shoes, Tobacco, Toys
**Content and Publishing**: Blogging Platforms, Content Delivery Network, Creative Agency, EBooks, Journalism, News, Photo Editing, Photo Sharing, Photography, Printing, Publishing, Video Editing, Video Streaming
**Data and Analytics**: Analytics, Application Performance Management, Artificial Intelligence, Big Data, Bioinformatics, Biometrics, Blockchain, Business Intelligence, Consumer Research, Data Integration, Data Mining, Data Visualization, Database, Ethereum, Geospatial, Image Recognition, Intelligent Systems, Location Based Services, Machine Learning, Market Research, Natural Language Processing, Predictive Analytics, Product Research, Real Time, Speech Recognition, Test and Measurement, Text Analytics, Usability Testing
**Design**: CAD, Consumer Research, Data Visualization, Fashion, Graphic Design, Human Computer Interaction, Industrial Design, Interior Design, Market Research, Mechanical Design, Product Design, Product Research, Usability Testing, UX Design, Web Design
**Education**: Charter Schools, Continuing Education, Corporate Training, E-Learning, EdTech, Education, Edutainment, Higher Education, Language Learning, Music Education, Personal Development, Primary Education, Secondary Education, Skill Assessment, STEM Education, Training, Tutoring, Universities, Vocational Education
**Energy**: Battery, Biofuel, Biomass Energy, Clean Energy, Electrical Distribution, Energy, Energy Efficiency, Energy Management, Energy Storage, Fuel, Oil and Gas, Power Grid, Renewable Energy, Solar, Wind Energy
**Events**: Concerts, Event Management, Event Promotion, Events, Reservations, Ticketing, Wedding
**Financial Services**: Accounting, Angel Investment, Asset Management, Auto Insurance, Banking, Bitcoin, Commercial Insurance, Commercial Lending, Consumer Lending, Credit, Credit Bureau, Credit Cards, Crowdfunding, Cryptocurrency, Debit Cards, Debt Collections, Finance, Financial Exchanges, Financial Services, FinTech, Fraud Detection, Funding Platform, Gift Card, Health Insurance, Hedge Funds, Impact Investing, Incubators, Insurance, InsurTech, Leasing, Lending, Life Insurance, Mobile Payments, Payments, Personal Finance, Property Insurance, Real Estate Investment, Stock Exchanges, Trading Platform, Transaction Processing, Venture Capital, Virtual Currency, Wealth Management
**Food and Beverage**: Bakery, Brewing, Cannabis, Catering, Coffee, Confectionery, Cooking, Craft Beer, Dietary Supplements, Distillery, Farmers Market, Food and Beverage, Food Delivery, Food Processing, Food Trucks, Fruit, Grocery, Nutrition, Organic Food, Recipes, Restaurants, Seafood, Snack Food, Tea, Tobacco, Wine And Spirits, Winery
**Gaming**: Casual Games, Console Games, Fantasy Sports, Gambling, Gamification, Gaming, Online Games, PC Games, Serious Games, Video Games, eSports
**Government and Military**: Government, GovTech, Law Enforcement, Military, National Security, Politics, Public Safety, Social Assistance
**Hardware**: 3D Technology, Augmented Reality, Cloud Infrastructure, Communication Hardware, Communications Infrastructure, Computer, Computer Vision, Consumer Electronics, Data Center, Data Center Automation, Data Storage, Drone Management, Drones, Electronic Design Automation (EDA), Electronics, Embedded Systems, GPS, Hardware, Industrial Design, Laser, Lighting, Mechanical Design, Mobile Devices, Network Hardware, Optical Communication, Private Cloud, Retail Technology, Robotics, Satellite Communication, Semiconductor, Sensor, Telecommunications, Video Conferencing, Virtual Reality, Virtualization, Wearables, Wireless
**Health Care**: Alternative Medicine, Assisted Living, Biopharma, Cannabis, Child Care, Clinical Trials, Cosmetic Surgery, Dental, Diabetes, Dietary Supplements, Elder Care, Electronic Health Record (EHR), Emergency Medicine, Employee Benefits, Fertility, First Aid, Funerals, Genetics, Health Care, Health Diagnostics, Home Health Care, Hospital, Medical, Medical Device, mHealth, Nursing and Residential Care, Nutrition, Outpatient Care, Personal Health, Pharmaceutical, Psychology, Rehabilitation, Therapeutics, Veterinary, Wellness
**Information Technology**: Business Information Systems, Cloud Data Services, Cloud Management, Cloud Security, CMS, Contact Management, CRM, Cyber Security, Data Center, Data Center Automation, Data Integration, Data Mining, Data Visualization, Document Management, Email, GovTech, Identity Management, Information and Communications Technology (ICT), Information Services, Information Technology, IT Infrastructure, IT Management, Management Information Systems, Messaging, Military, Network Security, Penetration Testing, Private Cloud, Reputation, Sales Automation, Scheduling, Unified Communications, Video Chat, Video Conferencing, Virtualization, VoIP
**Internet Services**: Cloud Computing, Cloud Data Services, Cloud Infrastructure, Cloud Management, Cloud Storage, Domain Registrar, E-Commerce Platforms, Email, Internet, Internet of Things, ISP, Location Based Services, Messaging, Music Streaming, Online Portals, Private Cloud, Search Engine, SEM, Semantic Search, SEO, SMS, Social Media, Social Media Management, Social Network, Unified Communications, Video Chat, Video Conferencing, VoIP, Web Hosting
**Lending and Investments**: Angel Investment, Banking, Commercial Lending, Consumer Lending, Credit, Credit Cards, Financial Exchanges, Funding Platform, Hedge Funds, Impact Investing, Incubators, Stock Exchanges, Trading Platform, Venture Capital
**Manufacturing**: 3D Printing, Advanced Materials, Foundries, Industrial Automation, Industrial Engineering, Industrial Manufacturing, Industrial, Infrastructure, Machinery Manufacturing, Manufacturing, Paper Manufacturing, Plastics and Rubber Manufacturing, Textiles, Wood Processing
**Media and Entertainment**: Animation, Art, Audio, Audiobooks, Blogging Platforms, Broadcasting, Concerts, Content, Content Creators, Creative Agency, Digital Entertainment, Digital Media, EBooks, Edutainment, Event Management, Event Promotion, Events, Film, Film Distribution, Film Production, Guides, Independent Music, Internet Radio, Journalism, Media and Entertainment, Motion Capture, Music, Music Education, Music Label, Music Streaming, Music Venues, Musical Instruments, News, Performing Arts, Photo Editing, Photo Sharing, Photography, Podcast, Printing, Publishing, Reservations, Social Media, Social News, Theatre, Ticketing, TV, TV Production, Video, Video Editing, Video on Demand, Video Streaming
**Messaging and Telecommunications**: Email, Meeting Software, Messaging, SMS, Unified Communications, Video Chat, Video Conferencing, VoIP, Wired Telecommunications
**Mobile**: Android, iOS, mHealth, Mobile, Mobile Apps, Mobile Devices, Mobile Payments, Wireless
**Music and Audio**: Audio, Audiobooks, Independent Music, Internet Radio, Music, Music Education, Music Label, Music Streaming, Musical Instruments, Podcast
**Natural Resources**: Biofuel, Biomass Energy, Mineral, Mining, Mining Technology, Natural Resources, Oil and Gas, Precious Metals, Solar, Timber, Water, Wind Energy
**Navigation and Mapping**: Geospatial, GPS, Location Based Services, Mapping Services, Navigation
**Payments**: Billing, Bitcoin, Credit Cards, Cryptocurrency, Debit Cards, Fraud Detection, Mobile Payments, Payments, Transaction Processing, Virtual Currency
**Platforms**: Android, iOS, Windows
**Privacy and Security**: Cloud Security, Cyber Security, Fraud Detection, Homeland Security, Identity Management, Law Enforcement, Network Security, Penetration Testing, Physical Security, Privacy, Security
**Professional Services**: Accounting, Advice, Business Development, Career Planning, Collaboration, Compliance, Consulting, Customer Service, Employment, Enterprise, Environmental Consulting, Field Support, Freelance, Human Resources, Innovation Management, Intellectual Property, Knowledge Management, Legal Tech, Legal, Management Consulting, Outsourcing, Personalization, Product Management, Professional Networking, Professional Services, Project Management, Quality Assurance, Recruiting, Risk Management, Service Industry, Small and Medium Businesses, Social Recruiting, Technical Support, Translation Service
**Real Estate**: Architecture, Building Maintenance, Building Material, Commercial Real Estate, Construction, Coworking, Facility Management, Fast-Moving Consumer Goods, Green Building, Home and Garden, Home Decor, Home Improvement, Home Renovation, Home Services, Interior Design, Janitorial Service, Landscaping, Property Development, Property Management, Real Estate Investment, Real Estate, Rental Property, Residential, Self-Storage, Smart Building, Smart Cities, Smart Home, Vacation Rental
**Sales and Marketing**: Advertising, Affiliate Marketing, App Marketing, Brand Marketing, Content Marketing, CRM, Digital Marketing, Digital Signage, Direct Marketing, Direct Sales, Email Marketing, Lead Generation, Lead Management, Loyalty Programs, Marketing, Marketing Automation, Mobile Advertising, Outdoor Advertising, Personal Branding, Public Relations, Sales, Sales Automation, SEM, SEO, Social Media Advertising, Social Media Management, Social Media Marketing, Video Advertising
**Science and Engineering**: Advanced Materials, Aerospace, Artificial Intelligence, Bioinformatics, Biometrics, Biopharma, Biotechnology, Chemical, Chemical Engineering, Civil Engineering, Embedded Systems, Environmental Engineering, Human Computer Interaction, Industrial Automation, Industrial Engineering, Intelligent Systems, Laser, Life Science, Marine Technology, Mechanical Engineering, Nanotechnology, Neuroscience, Nuclear, Quantum Computing, Robotics, Semiconductor, Software Engineering, STEM Education
**Software**: 3D Technology, Android, Application Performance Management, Apps, Artificial Intelligence, Augmented Reality, Billing, Bitcoin, CAD, Cloud Computing, Cloud Management, CMS, Computer Vision, Consumer Software, Contact Management, CRM, Cryptocurrency, Data Center Automation, Data Integration, Data Storage, Data Visualization, Database, Developer APIs, Developer Platform, Developer Tools, Document Management, Drone Management, E-Learning, EdTech, Electronic Design Automation (EDA), Embedded Systems, Enterprise Applications, Enterprise Resource Planning (ERP), Enterprise Software, File Sharing, IaaS, Image Recognition, iOS, Machine Learning, Marketing Automation, Meeting Software, Mobile Apps, Mobile Payments, Natural Language Processing, Open Source, PaaS, Predictive Analytics, Private Cloud, Productivity Tools, Retail Technology, Robotics, SaaS, Sales Automation, Scheduling, Simulation, Software, Software Engineering, Speech Recognition, Task Management, Text Analytics, Transaction Processing, Video Conferencing, Virtual Assistant, Virtual Currency, Virtual Reality, Virtualization, Web Apps, Web Development
**Sports**: American Football, Baseball, Basketball, Boating, Cycling, Diving, eSports, Fantasy Sports, Fitness, Golf, Hockey, Hunting, Outdoors, Racing, Recreation, Sailing, Skiing, Soccer, Sporting Goods, Sports, Surfing, Swimming, Tennis
**Sustainability**: Biofuel, Biomass Energy, Clean Energy, CleanTech, Energy Efficiency, Environmental Engineering, Green Building, GreenTech, Natural Resources, Organic, Pollution Control, Recycling, Renewable Energy, Solar, Sustainability, Waste Management, Water Purification, Wind Energy
**Transportation**: Air Transportation, Automotive, Autonomous Vehicles, Car Sharing, Courier Service, Delivery Service, Electric Vehicle, Fleet Management, Food Delivery, Freight Service, Last Mile Transportation, Limousine Service, Logistics, Marine Transportation, Parking, Ports and Harbors, Procurement, Public Transportation, Railroad, Recreational Vehicles, Ride Sharing, Same Day Delivery, Shipping, Space Travel, Supply Chain Management, Taxi Service, Transportation, Warehousing, Water Transportation
**Travel and Tourism**: Adventure Travel, Amusement Park and Arcade, Business Travel, Casino, Hospitality, Hotel, Museums and Historical Sites, Parks, Resorts, Tour Operator, Tourism, Travel, Travel Accommodations, Travel Agency, Vacation Rental
**Video**: Animation, Broadcasting, Film, Film Distribution, Film Production, Motion Capture, TV, TV Production, Video, Video Editing, Video on Demand, Video Streaming

## linkedinIndustries (248)

Accounting, Administration of Justice, Advertising Services, Airlines and Aviation, Airlines/Aviation, Alternative Dispute Resolution, Alternative Medicine, Animation, Animation and Post-production, Apparel & Fashion, Appliances, Electrical, and Electronics Manufacturing, Architecture & Planning, Architecture and Planning, Armed Forces, Artists and Writers, Arts and Crafts, Automation Machinery Manufacturing, Automotive, Aviation & Aerospace, Aviation and Aerospace Component Manufacturing, Banking, Beverage Manufacturing, Biotechnology, Biotechnology Research, Book and Periodical Publishing, Broadcast Media, Broadcast Media Production and Distribution, Building Materials, Business Consulting and Services, Business Supplies and Equipment, Capital Markets, Chemical Manufacturing, Chemicals, Civic & Social Organization, Civic and Social Organizations, Civil Engineering, Commercial Real Estate, Computer & Network Security, Computer Games, Computer Hardware, Computer Hardware Manufacturing, Computer Networking, Computer Networking Products, Computer Software, Computer and Network Security, Computers and Electronics Manufacturing, Construction, Consumer Electronics, Consumer Goods, Consumer Services, Cosmetics, Dairy, Dairy Product Manufacturing, Defense & Space, Defense and Space Manufacturing, Design, Design Services, E-Learning, E-Learning Providers, Education Administration Programs, Education Management, Electrical/Electronic Manufacturing, Entertainment, Entertainment Providers, Environmental Services, Events Services, Executive Office, Executive Offices, Facilities Services, Farming, Financial Services, Fine Art, Fisheries, Fishery, Food & Beverages, Food Production, Food and Beverage Manufacturing, Food and Beverage Services, Freight and Package Transportation, Fund-Raising, Fundraising, Furniture, Furniture and Home Furnishings Manufacturing, Gambling & Casinos, Gambling Facilities and Casinos, Glass, Ceramics & Concrete, Glass, Ceramics and Concrete Manufacturing, Government Administration, Government Relations, Government Relations Services, Graphic Design, Health, Wellness and Fitness, Higher Education, Hospital & Health Care, Hospitality, Hospitals and Health Care, Human Resources, Human Resources Services, IT Services and IT Consulting, Import and Export, Individual & Family Services, Individual and Family Services, Industrial Automation, Industrial Machinery Manufacturing, Information Services, Information Technology and Services, Insurance, International Affairs, International Trade and Development, Internet, Investment Banking, Investment Management, Judiciary, Law Enforcement, Law Practice, Leasing Non-residential Real Estate, Legal Services, Legislative Office, Legislative Offices, Leisure, Travel & Tourism, Libraries, Logistics and Supply Chain, Luxury Goods & Jewelry, Machinery, Machinery Manufacturing, Management Consulting, Manufacturing, Maritime, Maritime Transportation, Market Research, Marketing and Advertising, Mechanical or Industrial Engineering, Media Production, Medical Devices, Medical Equipment Manufacturing, Medical Practice, Medical Practices, Mental Health Care, Military, Mining, Mining & Metals, Mobile Games, Mobile Gaming Apps, Motion Pictures and Film, Motor Vehicle Manufacturing, Movies, Videos and Sound, Museums and Institutions, Museums, Historical Sites, and Zoos, Music, Musicians, Nanotechnology, Nanotechnology Research, Newspaper Publishing, Newspapers, Non-Profit Organization Management, Non-profit Organizations, Oil & Energy, Oil and Gas, Online Audio and Video Media, Online Media, Outsourcing and Offshoring Consulting, Outsourcing/Offshoring, Package/Freight Delivery, Packaging and Containers, Packaging and Containers Manufacturing, Paper & Forest Products, Paper and Forest Product Manufacturing, Performing Arts, Personal Care Product Manufacturing, Pharmaceutical Manufacturing, Pharmaceuticals, Philanthropic Fundraising Services, Philanthropy, Photography, Plastics, Plastics Manufacturing, Political Organization, Political Organizations, Primary and Secondary Education, Primary/Secondary Education, Printing, Printing Services, Professional Training & Coaching, Professional Training and Coaching, Program Development, Public Policy, Public Policy Offices, Public Relations and Communications, Public Relations and Communications Services, Public Safety, Publishing, Railroad Equipment Manufacturing, Railroad Manufacture, Ranching, Real Estate, Recreational Facilities, Recreational Facilities and Services, Religious Institutions, Renewable Energy Semiconductor Manufacturing, Renewables & Environment, Research, Research Services, Restaurants, Retail, Retail Apparel and Fashion, Retail Art Supplies, Retail Groceries, Retail Luxury Goods and Jewelry, Retail Office Equipment, Security and Investigations, Semiconductor Manufacturing, Semiconductors, Shipbuilding, Software Development, Spectator Sports, Sporting Goods, Sporting Goods Manufacturing, Sports, Staffing and Recruiting, Strategic Management Services, Supermarkets, Technology, Information and Internet, Telecommunications, Textile Manufacturing, Textiles, Think Tanks, Tobacco, Tobacco Manufacturing, Translation and Localization, Transportation, Logistics, Supply Chain and Storage, Transportation/Trucking/Railroad, Travel Arrangements, Truck Transportation, Utilities, Venture Capital & Private Equity, Venture Capital and Private Equity Principals, Veterinary, Veterinary Services, Warehousing, Warehousing and Storage, Wellness and Fitness Services, Wholesale, Wholesale Building Materials, Wholesale Import and Export, Wine and Spirits, Wireless, Wireless Services, Writing and Editing

## Estados de México (`states`/`includeRegions`, 32)

`mx-AGU`=Aguascalientes, `mx-BCN`=Baja California, `mx-BCS`=Baja California Sur, `mx-CAM`=Campeche, `mx-CHH`=Chihuahua, `mx-CHP`=Chiapas, `mx-CMX`=Mexico City, `mx-COA`=Coahuila, `mx-COL`=Colima, `mx-DUR`=Durango, `mx-GRO`=Guerrero, `mx-GUA`=Guanajuato, `mx-HID`=Hidalgo, `mx-JAL`=Jalisco, `mx-MEX`=State of Mexico, `mx-MIC`=Michoacán, `mx-MOR`=Morelos, `mx-NAY`=Nayarit, `mx-NLE`=Nuevo León, `mx-OAX`=Oaxaca, `mx-PUE`=Puebla, `mx-QUE`=Querétaro, `mx-ROO`=Quintana Roo, `mx-SIN`=Sinaloa, `mx-SLP`=San Luis Potosí, `mx-SON`=Sonora, `mx-TAB`=Tabasco, `mx-TAM`=Tamaulipas, `mx-TLA`=Tlaxcala, `mx-VER`=Veracruz, `mx-YUC`=Yucatán, `mx-ZAC`=Zacatecas

## Tecnologías

6,451 apps con categorías — demasiadas para listar: consultar `GET /v2/data-fields` (gratis) y filtrar por nombre/categoría.