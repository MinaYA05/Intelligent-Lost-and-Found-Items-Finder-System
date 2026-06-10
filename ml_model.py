import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer, ENGLISH_STOP_WORDS
from sklearn.metrics.pairwise import cosine_similarity
from sklearn.naive_bayes import MultinomialNB
from sklearn.pipeline import make_pipeline
import pickle
import os

class LostAndFoundModel:
    def __init__(self):
        # Add custom stop words relevant to lost and found context
        self.custom_stop_words = list(ENGLISH_STOP_WORDS) + [
            'lost', 'found', 'missing', 'missed', 'finding', 'losing', 
            'item', 'object', 'search', 'searching', 'looking', 'look'
        ]
        self.vectorizer = TfidfVectorizer(stop_words=self.custom_stop_words)
        self.category_classifier = None
        self.is_trained = False
        self.synonyms = self._get_synonyms()
        
        # Initial training data to warm-start the model
        # Categories must match report.html: Electronics, Accessories, Documents, Clothing, Books, Others
        self.initial_data = [
            # --- Electronics (100+ entries) ---
            # Generic / General Terms (Added for robustness)
            ("red phone", "Electronics"),
            ("blue phone", "Electronics"),
            ("black phone", "Electronics"),
            ("white phone", "Electronics"),
            ("green phone", "Electronics"),
            ("silver phone", "Electronics"),
            ("gold phone", "Electronics"),
            ("pink phone", "Electronics"),
            ("purple phone", "Electronics"),
            ("yellow phone", "Electronics"),
            ("mobile phone", "Electronics"),
            ("cell phone", "Electronics"),
            ("smartphone", "Electronics"),
            ("android phone", "Electronics"),
            ("flip phone", "Electronics"),
            ("old phone", "Electronics"),
            ("new phone", "Electronics"),
            ("broken phone", "Electronics"),
            ("found a phone", "Electronics"),
            ("lost a phone", "Electronics"),
            ("my phone", "Electronics"),
            ("iphone", "Electronics"),
            ("samsung phone", "Electronics"),
            ("nokia phone", "Electronics"),
            ("motorola phone", "Electronics"),
            ("lg phone", "Electronics"),
            ("google phone", "Electronics"),
            ("red mobile", "Electronics"),
            ("black mobile", "Electronics"),
            ("white mobile", "Electronics"),
            ("electronic device", "Electronics"),
            ("digital device", "Electronics"),
            ("gadget", "Electronics"),
            ("tablet device", "Electronics"),
            ("laptop computer", "Electronics"),
            ("camera device", "Electronics"),
            ("music player", "Electronics"),
            ("mp3 player", "Electronics"),
            ("smart watch", "Electronics"),
            ("fitness tracker", "Electronics"),
            ("headphones", "Electronics"),
            ("earbuds", "Electronics"),
            ("wireless charger", "Electronics"),
            ("power bank", "Electronics"),
            ("usb drive", "Electronics"),
            ("hard drive", "Electronics"),
            
            # Smartphones
            ("lost my iphone 13 pro max black case", "Electronics"),
            ("samsung galaxy s21 blue screen cracked", "Electronics"),
            ("google pixel 7 pro obsidian 128gb", "Electronics"),
            ("iphone 14 plus purple silicone case", "Electronics"),
            ("oneplus 10 pro emerald forest", "Electronics"),
            ("xiaomi redmi note 11 graphite gray", "Electronics"),
            ("sony xperia 1 iv black", "Electronics"),
            ("iphone se 3rd gen starlight", "Electronics"),
            ("samsung galaxy z flip 4 bora purple", "Electronics"),
            ("iphone 12 mini green", "Electronics"),
            ("motorola edge 30 ultra", "Electronics"),
            ("nokia g50 ocean blue", "Electronics"),
            ("iphone xr coral 64gb", "Electronics"),
            ("samsung galaxy s22 ultra phantom black", "Electronics"),
            ("huawei p50 pro cocoa gold", "Electronics"),
            
            # Laptops
            ("dell xps 15 laptop silver", "Electronics"),
            ("macbook pro 14 inch space grey m1", "Electronics"),
            ("hp spectre x360 convertible gem cut", "Electronics"),
            ("lenovo thinkpad x1 carbon gen 10", "Electronics"),
            ("asus rog zephyrus g14 gaming laptop", "Electronics"),
            ("acer swift 3 silver ultrabook", "Electronics"),
            ("microsoft surface laptop 5 sandstone", "Electronics"),
            ("razer blade 15 advanced model", "Electronics"),
            ("macbook air m2 midnight", "Electronics"),
            ("lg gram 17 inch white", "Electronics"),
            ("msi stealth gs66 gaming laptop", "Electronics"),
            ("samsung galaxy book2 pro 360", "Electronics"),
            ("dell inspiron 15 3000 series black", "Electronics"),
            ("hp pavilion 15 fog blue", "Electronics"),
            ("chromebook acer spin 713", "Electronics"),

            # Tablets
            ("ipad air 5th generation blue", "Electronics"),
            ("samsung galaxy tab s8 ultra", "Electronics"),
            ("microsoft surface pro 9 platinum", "Electronics"),
            ("ipad mini 6 pink", "Electronics"),
            ("amazon fire hd 10 tablet", "Electronics"),
            ("lenovo tab p11 pro gen 2", "Electronics"),
            ("ipad pro 12.9 inch m2 silver", "Electronics"),
            ("samsung galaxy tab a8 dark gray", "Electronics"),
            ("kindle paperwhite signature edition", "Electronics"),
            ("remarkable 2 e-ink tablet", "Electronics"),

            # Audio
            ("airpods pro 2nd gen white case", "Electronics"),
            ("sony wh-1000xm5 noise cancelling headphones", "Electronics"),
            ("bose quietcomfort 45 black", "Electronics"),
            ("jbl flip 6 bluetooth speaker red", "Electronics"),
            ("samsung galaxy buds 2 pro bora purple", "Electronics"),
            ("beats studio3 wireless matte black", "Electronics"),
            ("google pixel buds pro coral", "Electronics"),
            ("marshall emberton portable speaker", "Electronics"),
            ("senheiser momentum 4 wireless", "Electronics"),
            ("jabra elite 7 pro titanium black", "Electronics"),
            ("sonos roam smart speaker white", "Electronics"),
            ("anker soundcore liberty 4", "Electronics"),
            ("skullcandy crusher evo grey", "Electronics"),
            ("ue boom 3 waterproof speaker blue", "Electronics"),
            ("audio-technica ath-m50x black", "Electronics"),

            # Wearables
            ("apple watch series 8 midnight aluminum", "Electronics"),
            ("samsung galaxy watch 5 pro titanium", "Electronics"),
            ("fitbit charge 5 black fitness tracker", "Electronics"),
            ("garmin fenix 7 sapphire solar", "Electronics"),
            ("whoop 4.0 strap onyx", "Electronics"),
            ("oura ring gen 3 heritage gold", "Electronics"),
            ("apple watch ultra alpine loop", "Electronics"),
            ("google pixel watch polished silver", "Electronics"),
            ("fitbit versa 4 pink sand", "Electronics"),
            ("xiaomi mi band 7 black", "Electronics"),

            # Cameras & Drones
            ("canon eos r6 mirrorless camera body", "Electronics"),
            ("sony a7 iv full frame camera", "Electronics"),
            ("fujifilm x-t5 black body", "Electronics"),
            ("gopro hero 11 black action camera", "Electronics"),
            ("dji mini 3 pro drone with controller", "Electronics"),
            ("nikon z6 ii mirrorless camera", "Electronics"),
            ("instax mini 11 instant camera ice white", "Electronics"),
            ("polaroid now+ i-type camera blue", "Electronics"),
            ("dji mavic 3 classic drone", "Electronics"),
            ("ricoh gr iii street edition", "Electronics"),

            # Peripherals & Accessories
            ("logitech mx master 3s mouse pale gray", "Electronics"),
            ("keychron k2 mechanical keyboard", "Electronics"),
            ("apple magic trackpad black", "Electronics"),
            ("seagate portable external hard drive 2tb", "Electronics"),
            ("sandisk extreme portable ssd 1tb", "Electronics"),
            ("anker 737 power bank 24000mah", "Electronics"),
            ("apple magsafe charger white", "Electronics"),
            ("logitech c920 hd pro webcam", "Electronics"),
            ("blue yeti usb microphone blackout", "Electronics"),
            ("wacom intuos drawing tablet small", "Electronics"),
            ("usb-c hub anker 7-in-1", "Electronics"),
            ("samsung t7 shield ssd 2tb blue", "Electronics"),
            ("razer deathadder v3 pro mouse", "Electronics"),
            ("corsair k70 rgb mechanical keyboard", "Electronics"),
            ("elgato stream deck mk.2", "Electronics"),
            
            # Gaming
            ("nintendo switch oled model white", "Electronics"),
            ("playstation 5 dualsense controller white", "Electronics"),
            ("xbox series x wireless controller carbon black", "Electronics"),
            ("steam deck 512gb handheld console", "Electronics"),
            ("nintendo switch lite turquoise", "Electronics"),
            ("oculus quest 2 vr headset 128gb", "Electronics"),
            ("playstation portable psp black vintage", "Electronics"),
            ("gameboy advance sp blue", "Electronics"),
            ("logitech g cloud gaming handheld", "Electronics"),
            ("backbone one mobile controller playstation", "Electronics"),


            # --- Accessories (100+ entries) ---
            # Bags & Wallets
            ("brown leather wallet with id window", "Accessories"),
            ("michael kors tote bag jet set black", "Accessories"),
            ("herschel little america backpack grey", "Accessories"),
            ("fjallraven kanken backpack ochre", "Accessories"),
            ("coach wristlet wallet signature canvas", "Accessories"),
            ("louis vuitton speedy 30 monogram", "Accessories"),
            ("gucci marmont matelasse shoulder bag", "Accessories"),
            ("nike brasilia duffel bag small", "Accessories"),
            ("samsonite omni pc hardside spinner luggage", "Accessories"),
            ("north face borealis backpack black", "Accessories"),
            ("kate spade new york satchel pink", "Accessories"),
            ("tumi alpha 3 briefcase black", "Accessories"),
            ("bellroy slim sleeve wallet cocoa", "Accessories"),
            ("ridge wallet carbon fiber cash strap", "Accessories"),
            ("longchamp le pliage tote navy", "Accessories"),
            ("adidas alliance 2 sackpack blue", "Accessories"),
            ("jansport superbreak backpack red", "Accessories"),
            ("herschel novel duffel bag black", "Accessories"),
            ("swissgear travel gear scansmart backpack", "Accessories"),
            ("tory burch perry tote brown", "Accessories"),
            ("chanel classic flap bag black lambskin", "Accessories"),
            ("prada nylon backpack black", "Accessories"),
            ("bottega veneta woven wallet green", "Accessories"),
            ("goyard saint louis tote grey", "Accessories"),
            ("dagne dover neoprene backpack moss", "Accessories"),

            # Jewelry
            ("ring", "Accessories"),
            ("rings", "Accessories"),
            ("silver ring", "Accessories"),
            ("gold ring", "Accessories"),
            ("diamond ring", "Accessories"),
            ("engagement ring", "Accessories"),
            ("wedding ring", "Accessories"),
            ("earrings", "Accessories"),
            ("silver earrings", "Accessories"),
            ("gold earrings", "Accessories"),
            ("necklace", "Accessories"),
            ("gold necklace", "Accessories"),
            ("silver necklace", "Accessories"),
            ("bracelet", "Accessories"),
            ("jewelry", "Accessories"),
            ("jewellery", "Accessories"),
            ("pendant", "Accessories"),
            ("locket", "Accessories"),
            ("bangle", "Accessories"),
            ("anklet", "Accessories"),
            ("brooch", "Accessories"),
            ("gold necklace with heart pendant 14k", "Accessories"),
            ("silver hoop earrings sterling", "Accessories"),
            ("diamond engagement ring platinum band 1ct", "Accessories"),
            ("pandora charm bracelet silver", "Accessories"),
            ("cartier love bracelet yellow gold", "Accessories"),
            ("tiffany & co. heart tag necklace", "Accessories"),
            ("pearl stud earrings akoya", "Accessories"),
            ("swarovski crystal necklace blue", "Accessories"),
            ("men's gold chain cuban link", "Accessories"),
            ("wedding band tungsten carbide men's", "Accessories"),
            ("sapphire ring white gold halo", "Accessories"),
            ("emerald pendant necklace gold", "Accessories"),
            ("ruby stud earrings gold", "Accessories"),
            ("rolex submariner watch stainless steel", "Accessories"),
            ("omega speedmaster moonwatch professional", "Accessories"),
            ("seiko 5 automatic watch silver", "Accessories"),
            ("casio g-shock black digital watch", "Accessories"),
            ("fossil leather strap chronograph watch", "Accessories"),
            ("daniel wellington classic watch rose gold", "Accessories"),
            ("citizen eco-drive watch titanium", "Accessories"),
            ("tag heuer carrera watch automatic", "Accessories"),
            ("timex weekender watch nylon strap", "Accessories"),
            ("apple watch band milanese loop", "Accessories"), # Band is accessory
            ("fitbit band silicone replacement", "Accessories"),
            ("jade bangle bracelet green", "Accessories"),

            # Eyewear
            ("ray-ban aviator sunglasses gold frame", "Accessories"),
            ("oakley holbrook sunglasses matte black", "Accessories"),
            ("gucci oversized sunglasses tortoise", "Accessories"),
            ("prescription glasses warby parker", "Accessories"),
            ("reading glasses 2.0 strength blue", "Accessories"),
            ("maui jim polarized sunglasses", "Accessories"),
            ("tom ford eyeglasses black frame", "Accessories"),
            ("persol folding sunglasses havana", "Accessories"),
            ("contact lens case blue plastic", "Accessories"),
            ("sunglasses case hard shell black", "Accessories"),
            ("prada cinema sunglasses", "Accessories"),
            ("versace medusa sunglasses black", "Accessories"),
            ("blue light blocking glasses computer", "Accessories"),
            ("safety glasses clear protective", "Accessories"),
            ("swim goggles speedo vanquisher", "Accessories"),

            # Small Items
            ("pen", "Accessories"),
            ("blue pen", "Accessories"),
            ("black pen", "Accessories"),
            ("ballpoint pen", "Accessories"),
            ("fountain pen", "Accessories"),
            ("pencil", "Accessories"),
            ("mechanical pencil", "Accessories"),
            ("colored pencils", "Accessories"),
            ("marker", "Accessories"),
            ("highlighter", "Accessories"),
            ("sharpie", "Accessories"),
            ("stationery", "Accessories"),
            ("eraser", "Accessories"),
            ("pencil case", "Accessories"),
            ("stapler", "Accessories"),
            ("keys with a red keychain toyota", "Accessories"),
            ("house keys on a silver ring", "Accessories"),
            ("car key fob honda civic", "Accessories"),
            ("lanyard university of california blue", "Accessories"),
            ("keychain plush teddy bear brown", "Accessories"),
            ("swiss army knife victorinox red", "Accessories"),
            ("zippo lighter chrome finish", "Accessories"),
            ("fountain pen lamy safari charcoal", "Accessories"),
            ("ballpoint pen montblanc meisterstuck", "Accessories"),
            ("umbrella compact totes black", "Accessories"),
            ("umbrella golf size nike windproof", "Accessories"),
            ("belt leather brown reversible", "Accessories"),
            ("belt gucci marmont black leather", "Accessories"),
            ("scarf burberry giant check cashmere", "Accessories"),
            ("scarf silk floral print hermes", "Accessories"),
            ("gloves leather black cashmere lined", "Accessories"),
            ("mittens wool knit red patterns", "Accessories"),
            ("tie silk striped navy and red", "Accessories"),
            ("bowtie black satin formal", "Accessories"),
            ("pocket square white silk", "Accessories"),
            ("hair clip claw clip matte neutral", "Accessories"),
            ("hair tie scrunchie silk pink", "Accessories"),
            ("headband athletic nike dri-fit", "Accessories"),
            ("makeup bag cosmetic pouch glossier", "Accessories"),
            ("toiletry bag hanging travel organizer", "Accessories"),
            ("handkerchief cotton white monogram", "Accessories"),
            ("cufflinks silver square personalized", "Accessories"),
            ("money clip silver magnetic", "Accessories"),
            ("badge holder id reel retractable", "Accessories"),
            ("luggage tag leather personalized", "Accessories"),
            ("passport holder leather rfid blocking", "Accessories"),


            # --- Documents (100+ entries) ---
            # Generic
            ("papers", "Documents"),
            ("important papers", "Documents"),
            ("stack of papers", "Documents"),
            ("paperwork", "Documents"),
            ("document", "Documents"),
            ("documents", "Documents"),
            ("file", "Documents"),
            ("folder", "Documents"),
            ("manila folder", "Documents"),
            ("binder", "Documents"),
            ("notes", "Documents"),
            ("printed page", "Documents"),
            ("sheet of paper", "Documents"),
            ("letter", "Documents"),
            ("envelope", "Documents"),
            ("card", "Documents"),

            # Identification
            ("passport us citizen blue book", "Documents"),
            ("driver's license california real id", "Documents"),
            ("student id card university of texas", "Documents"),
            ("employee id badge hospital access", "Documents"),
            ("green card permanent resident card", "Documents"),
            ("social security card paper original", "Documents"),
            ("birth certificate certified copy", "Documents"),
            ("global entry card trusted traveler", "Documents"),
            ("military id card cac card", "Documents"),
            ("state id card new york", "Documents"),
            ("library card public library plastic", "Documents"),
            ("costco membership card gold star", "Documents"),
            ("aaa membership card roadside assistance", "Documents"),
            ("voter registration card", "Documents"),
            ("concealed carry permit license", "Documents"),

            # Financial
            ("credit card chase sapphire reserve metal", "Documents"),
            ("debit card bank of america red", "Documents"),
            ("amex platinum card metal", "Documents"),
            ("wells fargo debit card visa", "Documents"),
            ("citi double cash credit card", "Documents"),
            ("discover it card cashback", "Documents"),
            ("capital one venture card blue", "Documents"),
            ("checkbook leather cover bank checks", "Documents"),
            ("cash envelope with 500 dollars", "Documents"),
            ("travelers checks american express", "Documents"),
            ("gift card amazon 50 dollars", "Documents"),
            ("starbucks gift card reloadable", "Documents"),
            ("target gift card red bullseye", "Documents"),
            ("apple gift card app store", "Documents"),
            ("crypto hardware wallet recovery seed paper", "Documents"),

            # Official & Legal
            ("marriage certificate original copy", "Documents"),
            ("divorce decree legal papers", "Documents"),
            ("will and testament legal document", "Documents"),
            ("power of attorney notarized", "Documents"),
            ("property deed house title", "Documents"),
            ("car title pink slip vehicle", "Documents"),
            ("vehicle registration card dmv", "Documents"),
            ("insurance policy home state farm", "Documents"),
            ("auto insurance card geico", "Documents"),
            ("health insurance card blue cross", "Documents"),
            ("dental insurance card delta dental", "Documents"),
            ("medicare card red white blue", "Documents"),
            ("vaccination card covid-19 cdc", "Documents"),
            ("prescription paper doctor note", "Documents"),
            ("immigration form i-20 student visa", "Documents"),

            # Academic & Professional
            ("diploma university degree framed", "Documents"),
            ("transcript official academic grades", "Documents"),
            ("resume printed curriculum vitae", "Documents"),
            ("business cards stack professional", "Documents"),
            ("letter of recommendation sealed", "Documents"),
            ("contract employment agreement signed", "Documents"),
            ("nda non disclosure agreement", "Documents"),
            ("offer letter job acceptance", "Documents"),
            ("thesis paper spiral bound draft", "Documents"),
            ("research paper manuscript printed", "Documents"),
            ("syllabus course outline biology", "Documents"),
            ("exam paper scantron sheet", "Documents"),
            ("certificate of achievement award", "Documents"),
            ("professional license nursing board", "Documents"),
            ("teaching credential certificate", "Documents"),

            # Travel & Tickets
            ("boarding pass airline ticket delta", "Documents"),
            ("train ticket amtrak printed", "Documents"),
            ("bus pass monthly metro card", "Documents"),
            ("concert ticket taylor swift eras tour", "Documents"),
            ("movie ticket stub amc theaters", "Documents"),
            ("disneyland park hopper ticket", "Documents"),
            ("museum admission ticket louvre", "Documents"),
            ("hotel reservation confirmation printout", "Documents"),
            ("car rental agreement enterprise", "Documents"),
            ("cruise itinerary carnival cruise", "Documents"),
            ("baggage claim tag airline", "Documents"),
            ("parking pass permit hanging tag", "Documents"),
            ("ski lift ticket mammoth mountain", "Documents"),
            ("lottery ticket powerball numbers", "Documents"),
            ("raffle ticket strip red", "Documents"),

            # Mail & Paperwork
            ("utility bill electricity statement", "Documents"),
            ("water bill municipal services", "Documents"),
            ("internet bill comcast xfinity", "Documents"),
            ("tax return form 1040 irs", "Documents"),
            ("w2 form wage and tax statement", "Documents"),
            ("pay stub earnings statement", "Documents"),
            ("bank statement monthly account", "Documents"),
            ("lease agreement apartment rental", "Documents"),
            ("mortgage statement loan document", "Documents"),
            ("jury duty summons court paper", "Documents"),
            ("traffic ticket citation speeding", "Documents"),
            ("envelope sealed personal letter", "Documents"),
            ("postcard vintage travel souvenir", "Documents"),
            ("greeting card birthday hallmark", "Documents"),
            ("wedding invitation rsvp card", "Documents"),


            # --- Clothing (100+ entries) ---
            # Generic / Color + Item Combinations (Added for robustness)
            ("blue dress", "Clothing"),
            ("red dress", "Clothing"),
            ("black dress", "Clothing"),
            ("white dress", "Clothing"),
            ("green dress", "Clothing"),
            ("yellow dress", "Clothing"),
            ("pink dress", "Clothing"),
            ("purple dress", "Clothing"),
            ("orange dress", "Clothing"),
            ("patterned dress", "Clothing"),
            ("long dress", "Clothing"),
            ("short dress", "Clothing"),
            ("fancy dress", "Clothing"),
            ("casual dress", "Clothing"),
            ("my dress", "Clothing"),
            ("lost a dress", "Clothing"),
            ("found a dress", "Clothing"),
            ("blue shirt", "Clothing"),
            ("red shirt", "Clothing"),
            ("black shirt", "Clothing"),
            ("white shirt", "Clothing"),
            ("green shirt", "Clothing"),
            ("blue pants", "Clothing"),
            ("black pants", "Clothing"),
            ("jeans", "Clothing"),
            ("blue jeans", "Clothing"),
            ("black jeans", "Clothing"),
            ("jacket", "Clothing"),
            ("blue jacket", "Clothing"),
            ("black jacket", "Clothing"),
            ("coat", "Clothing"),
            ("shoes", "Clothing"),
            ("blue shoes", "Clothing"),
            ("black shoes", "Clothing"),
            ("sneakers", "Clothing"),
            ("hat", "Clothing"),
            ("scarf", "Clothing"),
            ("gloves", "Clothing"),
            ("socks", "Clothing"),
            ("underwear", "Clothing"),
            ("clothing item", "Clothing"),
            ("clothes", "Clothing"),
            ("garment", "Clothing"),
            ("apparel", "Clothing"),
            ("outfit", "Clothing"),
            ("costume", "Clothing"),

            # Cultural / Religious Clothing (Added for diversity)
            ("abaya", "Clothing"),
            ("black abaya", "Clothing"),
            ("white abaya", "Clothing"),
            ("hijab", "Clothing"),
            ("scarf hijab", "Clothing"),
            ("headscarf", "Clothing"),
            ("thobe", "Clothing"),
            ("white thobe", "Clothing"),
            ("kandura", "Clothing"),
            ("dishdasha", "Clothing"),
            ("kaftan", "Clothing"),
            ("jalabiya", "Clothing"),
            ("burqa", "Clothing"),
            ("niqab", "Clothing"),
            ("sari", "Clothing"),
            ("saree", "Clothing"),
            ("salwar kameez", "Clothing"),
            ("kurta", "Clothing"),
            ("lehenga", "Clothing"),
            ("sherwani", "Clothing"),
            ("kimono", "Clothing"),
            ("yukata", "Clothing"),
            ("hanbok", "Clothing"),
            ("cheongsam", "Clothing"),
            ("dirndl", "Clothing"),
            ("lederhosen", "Clothing"),
            ("kilt", "Clothing"),
            ("dashiki", "Clothing"),
            ("boubou", "Clothing"),
            ("poncho", "Clothing"),
            ("sarape", "Clothing"),
            ("sombrero", "Clothing"),
            ("turban", "Clothing"),
            ("fez", "Clothing"),
            ("kufi", "Clothing"),
            ("yarmulke", "Clothing"),
            ("kippah", "Clothing"),
            
            # Tops
            ("blue denim jacket levi's trucker", "Clothing"),
            ("black hoodie nike swoosh pullover", "Clothing"),
            ("white t-shirt cotton hanes large", "Clothing"),
            ("grey sweatshirt champion reverse weave", "Clothing"),
            ("flannel shirt red plaid button down", "Clothing"),
            ("polo shirt ralph lauren navy", "Clothing"),
            ("blouse silk white floral print", "Clothing"),
            ("sweater cashmere beige v-neck", "Clothing"),
            ("cardigan wool grey button up", "Clothing"),
            ("tank top athletic racerback black", "Clothing"),
            ("tunic top bohemian style patterned", "Clothing"),
            ("crop top white cotton rib knit", "Clothing"),
            ("turtleneck sweater black merino wool", "Clothing"),
            ("hawaiian shirt tropical print blue", "Clothing"),
            ("graphic tee band shirt nirvana", "Clothing"),

            # Outerwear
            ("winter coat north face puffer black", "Clothing"),
            ("trench coat beige burberry classic", "Clothing"),
            ("leather jacket motorcycle style black", "Clothing"),
            ("raincoat yellow waterproof columbia", "Clothing"),
            ("windbreaker jacket nike lightweight", "Clothing"),
            ("pea coat navy wool double breasted", "Clothing"),
            ("bomber jacket olive green alpha industries", "Clothing"),
            ("parka canada goose fur hood", "Clothing"),
            ("vest puffer down filled patagonia", "Clothing"),
            ("blazer jacket navy blue suit separate", "Clothing"),
            ("fleece jacket patagonia snap-t", "Clothing"),
            ("jean jacket oversized vintage wash", "Clothing"),
            ("ski jacket spider red and black", "Clothing"),
            ("rain poncho clear plastic disposable", "Clothing"),
            ("overcoat wool long camel color", "Clothing"),

            # Bottoms
            ("jeans levi's 501 original fit blue", "Clothing"),
            ("jeans skinny black high waisted", "Clothing"),
            ("leggings lululemon align black", "Clothing"),
            ("joggers nike tech fleece grey", "Clothing"),
            ("shorts denim distressed daisy dukes", "Clothing"),
            ("shorts athletic gym nike dri-fit", "Clothing"),
            ("chinos khaki pants slim fit gap", "Clothing"),
            ("dress pants wool charcoal grey", "Clothing"),
            ("skirt pencil black office wear", "Clothing"),
            ("skirt mini plaid pleated schoolgirl", "Clothing"),
            ("maxi skirt floral bohemian style", "Clothing"),
            ("cargo pants green utility pockets", "Clothing"),
            ("sweatpants grey cotton champion", "Clothing"),
            ("corduroy pants brown straight leg", "Clothing"),
            ("biker shorts black spandex", "Clothing"),

            # Dresses & Suits
            ("summer dress floral sundress spaghetti strap", "Clothing"),
            ("little black dress cocktail party", "Clothing"),
            ("maxi dress bohemian long sleeve", "Clothing"),
            ("wrap dress diane von furstenberg pattern", "Clothing"),
            ("prom dress sequin gown blue", "Clothing"),
            ("wedding dress white lace gown", "Clothing"),
            ("bridesmaid dress pink chiffon", "Clothing"),
            ("suit men's charcoal grey wool slim", "Clothing"),
            ("tuxedo black formal wear satin lapel", "Clothing"),
            ("jumpsuit denim utility style", "Clothing"),
            ("romper floral summer shorts", "Clothing"),
            ("kimono silk robe japanese style", "Clothing"),
            ("sari silk traditional indian red", "Clothing"),
            ("kilt wool tartan scottish", "Clothing"),
            ("uniform school polo and skirt set", "Clothing"),

            # Footwear
            ("sneakers nike air force 1 white", "Clothing"),
            ("running shoes adidas ultraboost black", "Clothing"),
            ("converse chuck taylor high top black", "Clothing"),
            ("vans old skool skate shoes checkered", "Clothing"),
            ("boots timberland 6 inch wheat", "Clothing"),
            ("boots dr martens 1460 black leather", "Clothing"),
            ("chelsea boots brown suede blundstone", "Clothing"),
            ("uggs classic short boots chestnut", "Clothing"),
            ("heels pumps black leather louboutin", "Clothing"),
            ("sandals birkenstock arizona brown", "Clothing"),
            ("flip flops havaianas rubber blue", "Clothing"),
            ("slides adidas adilette comfort stripes", "Clothing"),
            ("loafers gucci horsebit leather black", "Clothing"),
            ("boat shoes sperry top sider leather", "Clothing"),
            ("crocs classic clog white", "Clothing"),
            ("hiking boots merrell moab waterproof", "Clothing"),
            ("soccer cleats nike mercurial pink", "Clothing"),
            ("cowboy boots leather western style", "Clothing"),
            ("rain boots hunter tall glossy black", "Clothing"),
            ("slippers ugg scuffette sheepskin", "Clothing"),

            # Accessories (Wearable) & Intimates
            ("socks nike crew socks white 6 pack", "Clothing"),
            ("socks wool hiking smartwool grey", "Clothing"),
            ("socks ankle no show black cotton", "Clothing"),
            ("tights black opaque nylon", "Clothing"),
            ("stockings sheer nude nylon", "Clothing"),
            ("boxer briefs calvin klein black", "Clothing"),
            ("bra victoria secret push up pink", "Clothing"),
            ("sports bra nike swoosh black", "Clothing"),
            ("bikini swimsuit two piece blue floral", "Clothing"),
            ("swim trunks boardshorts hurley pattern", "Clothing"),
            ("one piece swimsuit speedo black", "Clothing"),
            ("wetsuit o'neill full suit neoprene", "Clothing"),
            ("rash guard swim shirt uv protection", "Clothing"),
            ("hat baseball cap ny yankees navy", "Clothing"),
            ("beanie knit cap carhartt acrylic", "Clothing"),


            # --- Books (100+ entries) ---
            # Generic / General Terms (Added for robustness)
            ("book", "Books"),
            ("books", "Books"),
            ("textbook", "Books"),
            ("textbooks", "Books"),
            ("notebook", "Books"),
            ("notebooks", "Books"),
            ("diary", "Books"),
            ("diaries", "Books"),
            ("journal", "Books"),
            ("journals", "Books"),
            ("novel", "Books"),
            ("novels", "Books"),
            ("paperback", "Books"),
            ("hardcover", "Books"),
            ("encyclopedia", "Books"),
            ("dictionary", "Books"),
            ("bible", "Books"),
            ("quran", "Books"),
            ("scripture", "Books"),
            ("magazine", "Books"),
            ("comic", "Books"),
            ("manga", "Books"),
            ("album", "Books"),
            ("planner", "Books"),
            ("agenda", "Books"),
            ("sketchbook", "Books"),
            ("found a book", "Books"),
            ("lost a book", "Books"),
            ("my book", "Books"),
            ("reading book", "Books"),
            ("school book", "Books"),
            ("story book", "Books"),
            ("writing book", "Books"),

            # Textbooks & Education
            ("textbook introduction to algorithms cormen", "Books"),
            ("textbook calculus early transcendentals stewart", "Books"),
            ("textbook organic chemistry klein", "Books"),
            ("textbook physics for scientists engineers", "Books"),
            ("textbook campbell biology 11th edition", "Books"),
            ("textbook psychology myers 12th edition", "Books"),
            ("textbook macroeconomics mankiw", "Books"),
            ("textbook computer networks tanenbaum", "Books"),
            ("textbook principles of marketing kotler", "Books"),
            ("textbook history of western society", "Books"),
            ("workbook japanese language genki", "Books"),
            ("sat prep book college board official", "Books"),
            ("mcat complete study package kaplan", "Books"),
            ("lsat prep books powerscore bible", "Books"),
            ("dictionary oxford english hardcover", "Books"),
            ("thesaurus roget's international", "Books"),
            ("encyclopedia britannica volume set", "Books"),
            ("atlas of the world national geographic", "Books"),
            ("lab manual chemistry experiments", "Books"),
            ("sheet music book piano classical mozart", "Books"),

            # Fiction
            ("novel harry potter and the sorcerer's stone", "Books"),
            ("novel to kill a mockingbird harper lee", "Books"),
            ("novel the great gatsby f scott fitzgerald", "Books"),
            ("novel 1984 george orwell paperback", "Books"),
            ("novel pride and prejudice jane austen", "Books"),
            ("novel the catcher in the rye salinger", "Books"),
            ("novel the hobbit jrr tolkien", "Books"),
            ("novel lord of the rings fellowship ring", "Books"),
            ("novel game of thrones george rr martin", "Books"),
            ("novel the da vinci code dan brown", "Books"),
            ("novel gone girl gillian flynn", "Books"),
            ("novel the hunger games suzanne collins", "Books"),
            ("novel twilight stephenie meyer", "Books"),
            ("novel the alchemist paulo coelho", "Books"),
            ("novel the kite runner khaled hosseini", "Books"),
            ("novel brave new world aldous huxley", "Books"),
            ("novel fahrenheit 451 ray bradbury", "Books"),
            ("novel animal farm george orwell", "Books"),
            ("novel the book thief markus zusak", "Books"),
            ("novel life of pi yann martel", "Books"),
            ("novel dune frank herbert sci-fi", "Books"),
            ("novel it stephen king horror", "Books"),
            ("novel the shining stephen king", "Books"),
            ("novel percy jackson lightning thief", "Books"),
            ("novel the fault in our stars john green", "Books"),

            # Non-Fiction
            ("biography steve jobs walter isaacson", "Books"),
            ("memoir becoming michelle obama", "Books"),
            ("book sapiens a brief history of humankind", "Books"),
            ("book educated a memoir tara westover", "Books"),
            ("book thinking fast and slow kahneman", "Books"),
            ("book atomic habits james clear", "Books"),
            ("book the power of habit charles duhigg", "Books"),
            ("book quiet the power of introverts", "Books"),
            ("book outliers the story of success gladwell", "Books"),
            ("book born a crime trevor noah", "Books"),
            ("cookbook salt fat acid heat nosrat", "Books"),
            ("cookbook joy of cooking rombauer", "Books"),
            ("cookbook mastering the art of french cooking", "Books"),
            ("book how to win friends and influence people", "Books"),
            ("book rich dad poor dad kiyosaki", "Books"),
            ("book the 4-hour workweek tim ferriss", "Books"),
            ("book into the wild jon krakauer", "Books"),
            ("book a brief history of time hawking", "Books"),
            ("book cosmos carl sagan", "Books"),
            ("book guns germs and steel diamond", "Books"),

            # Personal & Miscellaneous
            ("journal moleskine black classic notebook", "Books"),
            ("diary locked pink floral with key", "Books"),
            ("notebook spiral bound 5 subject mead", "Books"),
            ("planner 2023 daily calendar agenda", "Books"),
            ("sketchbook strathmore drawing paper", "Books"),
            ("composition notebook marble cover", "Books"),
            ("legal pad yellow writing tablet", "Books"),
            ("bible holy scriptures niv leather", "Books"),
            ("quran holy book arabic english", "Books"),
            ("torah scroll book hebrew", "Books"),
            ("comic book spider-man marvel issue", "Books"),
            ("comic book batman dc detective comics", "Books"),
            ("manga naruto volume 1 paperback", "Books"),
            ("manga one piece volume 100", "Books"),
            ("graphic novel maus art spiegelman", "Books"),
            ("magazine vogue fashion monthly issue", "Books"),
            ("magazine national geographic yellow border", "Books"),
            ("magazine time person of the year", "Books"),
            ("magazine sports illustrated swimsuit", "Books"),
            ("magazine new yorker weekly", "Books"),
            ("catalog ikea furniture home", "Books"),
            ("brochure travel guide paris", "Books"),
            ("coloring book adult mandala stress relief", "Books"),
            ("puzzle book sudoku crosswords", "Books"),
            ("photo album leather bound family pictures", "Books"),


            # --- Others (100+ entries) ---
            # Animals / Pets
            ("dog golden retriever puppy cream color", "Others"),
            ("dog labrador retriever black male", "Others"),
            ("dog german shepherd adult police dog", "Others"),
            ("dog french bulldog brindle", "Others"),
            ("dog poodle white toy size", "Others"),
            ("dog chihuahua tan short hair", "Others"),
            ("dog husky siberian blue eyes", "Others"),
            ("dog beagle tri-color floppy ears", "Others"),
            ("dog dachshund wiener dog brown", "Others"),
            ("dog pitbull terrier grey muscular", "Others"),
            ("cat persian white fluffy long hair", "Others"),
            ("cat siamese blue eyes cream body", "Others"),
            ("cat maine coon large tabby", "Others"),
            ("cat bengal spotted leopard print", "Others"),
            ("cat sphynx hairless pink skin", "Others"),
            ("cat ragdoll blue point fluffy", "Others"),
            ("cat british shorthair grey chubby", "Others"),
            ("cat scottish fold folded ears", "Others"),
            ("cat tuxedo black and white domestic", "Others"),
            ("cat calico tri-color female", "Others"),
            ("bird parrot macaw red and blue", "Others"),
            ("bird cockatiel yellow crest grey", "Others"),
            ("bird parakeet budgie blue and white", "Others"),
            ("bird canary yellow singer", "Others"),
            ("rabbit holland lop floppy ears grey", "Others"),
            ("hamster syrian golden fluffy", "Others"),
            ("guinea pig american tri-color", "Others"),
            ("ferret sable bandit mask", "Others"),
            ("turtle red-eared slider aquatic", "Others"),
            ("tortoise russian land turtle", "Others"),
            ("lizard bearded dragon orange spiked", "Others"),
            ("snake ball python royal python", "Others"),
            ("fish goldfish comet orange", "Others"),
            ("fish betta siamese fighting fish blue", "Others"),

            # Sports & Outdoors
            ("yoga mat lululemon purple 5mm", "Others"),
            ("tennis racket wilson pro staff red", "Others"),
            ("tennis balls can of 3 penn", "Others"),
            ("football wilson nfl official leather", "Others"),
            ("basketball spalding nba official orange", "Others"),
            ("soccer ball adidas world cup white", "Others"),
            ("baseball glove rawlings leather mitt", "Others"),
            ("baseball bat louisville slugger wood", "Others"),
            ("golf clubs set callaway with bag", "Others"),
            ("golf ball titleist pro v1 white", "Others"),
            ("skateboard santa cruz screaming hand", "Others"),
            ("longboard sector 9 bamboo", "Others"),
            ("bicycle trek mountain bike blue", "Others"),
            ("bicycle helmet giro matte black", "Others"),
            ("scooter razor kick scooter silver", "Others"),
            ("rollerblades inline skates black", "Others"),
            ("surfboard longboard fiberglass white", "Others"),
            ("snowboard burton custom flying v", "Others"),
            ("skis salomon with bindings", "Others"),
            ("tent coleman 4 person dome green", "Others"),
            ("sleeping bag mummy style north face", "Others"),
            ("camping chair folding blue", "Others"),
            ("cooler yeti tundra 45 white", "Others"),
            ("water bottle hydro flask yellow 32oz", "Others"),
            ("thermos stanley classic green vacuum", "Others"),

            # Tools & Hardware
            ("hammer claw hammer stanley wooden handle", "Others"),
            ("screwdriver set craftsman phillips flat", "Others"),
            ("wrench adjustable crescent silver", "Others"),
            ("pliers needle nose red handle", "Others"),
            ("drill dewalt cordless yellow 20v", "Others"),
            ("tape measure stanley 25ft fatmax", "Others"),
            ("saw hand saw wood cutting", "Others"),
            ("flashlight maglite heavy duty black", "Others"),
            ("pocket knife swiss army red", "Others"),
            ("leatherman multi-tool stainless steel", "Others"),
            ("ladder aluminum folding 6ft", "Others"),
            ("toolbox metal red portable", "Others"),
            ("extension cord orange heavy duty", "Others"),
            ("padlock master lock combination", "Others"),
            ("batteries duracell aa pack", "Others"),

            # Musical Instruments
            ("guitar acoustic fender dreadnought natural", "Others"),
            ("guitar electric gibson les paul sunburst", "Others"),
            ("ukulele soprano wood brown", "Others"),
            ("violin stradivarius copy with bow", "Others"),
            ("piano keyboard yamaha digital 88 keys", "Others"),
            ("trumpet brass yamaha student model", "Others"),
            ("flute silver plated open hole", "Others"),
            ("saxophone alto brass selmer", "Others"),
            ("drum set pearl export black", "Others"),
            ("drum sticks vic firth wood", "Others"),
            ("harmonica hohner blues harp", "Others"),
            ("microphone stand boom arm black", "Others"),
            ("music stand folding metal black", "Others"),
            ("guitar case hard shell black", "Others"),
            ("metronome digital tuner korg", "Others"),

            # Household & Miscellaneous
            ("lunch box insulated bag blue", "Others"),
            ("bento box plastic divider container", "Others"),
            ("tupperware container set plastic lids", "Others"),
            ("mug coffee cup ceramic white", "Others"),
            ("tumbler starbucks cold cup straw", "Others"),
            ("pillow memory foam neck support", "Others"),
            ("blanket fleece throw grey soft", "Others"),
            ("towel beach towel striped colors", "Others"),
            ("umbrella patio sun shade beige", "Others"),
            ("vase glass flower vase clear", "Others"),
            ("picture frame wood 8x10 black", "Others"),
            ("candle scented jar yankee candle", "Others"),
            ("plant potted succulent green ceramic", "Others"),
            ("plant artificial ficus tree indoor", "Others"),
            ("clock wall clock analog round", "Others"),
            ("mirror vanity mirror lighted makeup", "Others"),
            ("rug area rug persian pattern red", "Others"),
            ("curtains blackout panels grey", "Others"),
            ("lamp desk lamp led adjustable", "Others"),
            ("fan portable desk fan usb", "Others"),
            ("heater space heater ceramic electric", "Others"),
            ("vacuum cleaner dyson stick cordless", "Others"),
            ("iron clothes iron steam black and decker", "Others"),
            ("sewing machine brother computerized", "Others"),
            ("yarn knitting wool balls colorful", "Others"),

            # Medical Aids
            ("wheelchair manual folding standard", "Others"),
            ("crutches aluminum adjustable pair", "Others"),
            ("cane walking stick wooden handle", "Others"),
            ("walker folding with wheels grey", "Others"),
            ("hearing aid digital beige in ear", "Others"),
            ("glasses case hard shell black", "Others"),
            ("pill organizer weekly box plastic", "Others"),
            ("blood pressure monitor cuff digital", "Others"),
            ("stethoscope littmann classic black", "Others"),
            ("brace knee brace compression black", "Others"),

            # Toys & Games
            ("teddy bear plush stuffed animal brown", "Others"),
            ("lego set star wars millennium falcon", "Others"),
            ("barbie doll blonde pink dress", "Others"),
            ("action figure marvel spiderman", "Others"),
            ("hot wheels car diecast metal toy", "Others"),
            ("board game monopoly classic edition", "Others"),
            ("board game scrabble crossword game", "Others"),
            ("board game catan settlement", "Others"),
            ("card game uno deck colorful", "Others"),
            ("card game playing cards bicycle deck", "Others"),
            ("puzzle jigsaw 1000 pieces landscape", "Others"),
            ("rubiks cube 3x3 puzzle toy", "Others"),
            ("drone toy quadcopter remote control", "Others"),
            ("nerf gun blaster foam darts", "Others"),
            ("dollhouse wooden furniture set", "Others")
        ]
        
        # Train on initial data immediately
        self._train_initial_model()

    def _train_initial_model(self):
        """Train the model on initial hardcoded data"""
        texts, labels = zip(*self.initial_data)
        self.category_classifier = make_pipeline(TfidfVectorizer(stop_words=self.custom_stop_words), MultinomialNB())
        self.category_classifier.fit(texts, labels)
        self.is_trained = True
        print("ML Model initialized and trained on basic dataset.")

    def train(self, items):
        """
        Retrain the model with new data from database
        items: list of dicts with 'description' and 'category'
        """
        if not items:
            return
            
        texts = [f"{item['item_name']} {item['description']}" for item in items]
        labels = [item['category'] for item in items]
        
        # Combine with initial data to maintain baseline knowledge
        initial_texts, initial_labels = zip(*self.initial_data)
        texts.extend(initial_texts)
        labels.extend(initial_labels)
        
        self.category_classifier.fit(texts, labels)
        self.is_trained = True
        print(f"Model retrained on {len(items)} database items + {len(self.initial_data)} initial items.")

    def predict_category(self, description):
        """Predict category for a given description"""
        if not self.is_trained:
            self._train_initial_model()
            
        # Expand description with synonyms to help classification
        expanded_desc = self._expand_text(description)
        
        prediction = self.category_classifier.predict([expanded_desc])[0]
        probabilities = self.category_classifier.predict_proba([expanded_desc])[0]
        confidence = max(probabilities)
        
        return {
            'category': prediction,
            'confidence': float(confidence)
        }

    def _get_synonyms(self):
        """Return the dictionary of synonyms"""
        return {
            # --- ELECTRONICS ---
            # Phones & Tablets
            'phone': ['mobile', 'smartphone', 'cellphone', 'iphone', 'android', 'device', 'handset', 'cellular', 'telephone'],
            'mobile': ['phone', 'smartphone', 'cellphone', 'iphone', 'android', 'device', 'handset', 'cellular', 'telephone'],
            'smartphone': ['phone', 'mobile', 'android', 'iphone', 'device', 'handset'],
            'device': ['electronics', 'gadget', 'phone', 'mobile', 'camera', 'laptop', 'computer', 'tablet', 'watch', 'console', 'technology'],
            'cellphone': ['phone', 'mobile', 'handset'],
            'iphone': ['phone', 'mobile', 'smartphone', 'apple', 'ios', 'device', 'iphone12', 'iphone13', 'iphone14', 'iphone15', 'promax', 'mini'],
            'android': ['phone', 'mobile', 'smartphone', 'samsung', 'google', 'pixel', 'oneplus', 'xiaomi', 'huawei', 'oppo', 'vivo', 'motorola', 'nokia', 'sony', 'lg'],
            'samsung': ['phone', 'mobile', 'android', 'galaxy', 'smartphone'],
            'pixel': ['phone', 'mobile', 'android', 'google', 'smartphone'],
            'xiaomi': ['phone', 'mobile', 'android', 'redmi', 'smartphone'],
            'oneplus': ['phone', 'mobile', 'android', 'smartphone'],
            'huawei': ['phone', 'mobile', 'android', 'smartphone'],
            'nokia': ['phone', 'mobile', 'android', 'smartphone'],
            'motorola': ['phone', 'mobile', 'android', 'moto', 'smartphone'],
            'oppo': ['phone', 'mobile', 'android', 'smartphone'],
            'vivo': ['phone', 'mobile', 'android', 'smartphone'],
            'tablet': ['ipad', 'tab', 'kindle', 'reader', 'device', 'surface', 'slate', 'phablet'],
            'ipad': ['tablet', 'apple', 'ios', 'device', 'air', 'pro', 'mini'],
            'kindle': ['tablet', 'reader', 'amazon', 'ebook', 'paperwhite', 'oasis'],
            
            # Computers & Laptops
            'laptop': ['computer', 'notebook', 'macbook', 'pc', 'device', 'dell', 'hp', 'lenovo', 'asus', 'acer', 'msi', 'razer', 'chromebook', 'thinkpad', 'inspiron', 'pavilion', 'yoga', 'surface', 'alienware'],
            'computer': ['laptop', 'desktop', 'pc', 'macbook', 'device', 'system', 'machine', 'workstation', 'monitor', 'cpu'],
            'macbook': ['laptop', 'computer', 'apple', 'mac', 'air', 'pro'],
            'pc': ['computer', 'laptop', 'desktop', 'windows', 'tower'],
            'desktop': ['computer', 'pc', 'tower', 'monitor', 'workstation', 'imac'],
            'keyboard': ['keypad', 'typing', 'input', 'mechanical', 'membrane', 'wireless', 'bluetooth', 'logitech', 'corsair', 'razer'],
            'mouse': ['pointer', 'clicker', 'peripheral', 'optical', 'wireless', 'bluetooth', 'trackpad', 'logitech', 'razer'],
            'monitor': ['screen', 'display', 'led', 'lcd', 'oled', 'computer', 'desktop', 'samsung', 'lg', 'dell', 'hp'],
            'printer': ['scanner', 'copier', 'machine', 'hp', 'canon', 'epson', 'brother', 'laser', 'inkjet'],
            
            # Cameras & Photography
            'camera': ['dslr', 'cam', 'photo', 'video', 'lens', 'device', 'canon', 'nikon', 'sony', 'fujifilm', 'panasonic', 'olympus', 'gopro', 'polaroid', 'webcam', 'camcorder', 'mirrorless'],
            'dslr': ['camera', 'canon', 'nikon', 'sony', 'photo'],
            'lens': ['camera', 'glass', 'zoom', 'prime', 'telephoto', 'macro', 'wide', 'canon', 'nikon', 'sony', 'sigma', 'tamron'],
            'gopro': ['camera', 'action', 'video', 'hero'],
            'drone': ['quadcopter', 'uav', 'camera', 'dji', 'mavic', 'phantom', 'mini', 'air'],
            
            # Audio
            'headphones': ['earbuds', 'headset', 'earphones', 'cans', 'audio', 'sony', 'bose', 'sennheiser', 'beats', 'jbl', 'skullcandy'],
            'earbuds': ['headphones', 'airpods', 'earphones', 'buds', 'wireless', 'bluetooth', 'tws', 'galaxybuds', 'pixelbuds'],
            'airpods': ['earbuds', 'headphones', 'apple', 'pro', 'max'],
            'speaker': ['audio', 'sound', 'bluetooth', 'jbl', 'bose', 'sonos', 'marshall', 'ue', 'soundbar', 'woofer', 'subwoofer'],
            'microphone': ['mic', 'audio', 'recording', 'voice', 'blue', 'yeti', 'shure', 'rode'],
            
            # Accessories & Components
            'charger': ['adapter', 'cable', 'cord', 'plug', 'power', 'wire', 'usb', 'lightning', 'usbc', 'magsafe', 'brick', 'block'],
            'cable': ['cord', 'wire', 'lead', 'usb', 'hdmi', 'ethernet', 'aux', 'lightning'],
            'battery': ['power', 'cell', 'pack', 'bank', 'portable', 'charging', 'duracell', 'energizer'],
            'powerbank': ['battery', 'charger', 'portable', 'anker', 'xiaomi'],
            'harddrive': ['storage', 'disk', 'ssd', 'hdd', 'external', 'drive', 'usb', 'seagate', 'wd', 'sandisk', 'samsung'],
            'usb': ['flash', 'drive', 'stick', 'thumb', 'pendrive', 'storage', 'memory'],
            # Boost electronics/gadget to ensure "device" matches category "Electronics" strongly
            'device': ['electronics', 'gadget', 'phone', 'mobile', 'camera', 'laptop', 'computer', 'tablet', 'watch', 'console', 'technology'],
            'electronics': ['device', 'gadget', 'technology', 'digital', 'electric'],
            'gadget': ['device', 'electronics', 'tool', 'toy', 'gizmo'],
            
            # Gaming
            'console': ['gaming', 'game', 'playstation', 'xbox', 'nintendo', 'switch', 'ps4', 'ps5', 'seriesx', 'wii'],
            'controller': ['gamepad', 'joystick', 'remote', 'dualshock', 'dualsense', 'joycon'],
            'game': ['disc', 'cartridge', 'video', 'software', 'cd', 'dvd', 'bluray'],

            # --- ACCESSORIES ---
            # Bags & Luggage
            'bag': ['backpack', 'purse', 'handbag', 'suitcase', 'luggage', 'tote', 'satchel', 'messenger', 'duffel', 'clutch', 'pouch', 'sack', 'briefcase', 'carrier'],
            'backpack': ['bag', 'luggage', 'schoolbag', 'rucksack', 'knapsack', 'daypack', 'jansport', 'northface', 'nike', 'adidas'],
            'handbag': ['bag', 'purse', 'tote', 'shoulder', 'clutch', 'designer', 'gucci', 'prada', 'lv', 'michaelkors'],
            'suitcase': ['bag', 'luggage', 'travel', 'trolley', 'roller', 'carryon', 'samsonite', 'rimowa', 'american'],
            'briefcase': ['bag', 'case', 'leather', 'business', 'laptop'],
            
            # Wallets & Money
            'wallet': ['purse', 'cardholder', 'billfold', 'money', 'pouch', 'leather', 'bi-fold', 'tri-fold'],
            'purse': ['wallet', 'bag', 'handbag', 'money', 'clutch', 'coin'],
            'money': ['cash', 'wallet', 'currency', 'notes', 'coins', 'bills', 'change'],
            'card': ['credit', 'debit', 'atm', 'visa', 'mastercard', 'id', 'amex', 'bank', 'membership', 'gift'],
            
            # Jewelry & Watches
            'jewelry': ['necklace', 'ring', 'bracelet', 'earring', 'pendant', 'chain', 'gold', 'silver', 'diamond', 'platinum', 'gemstone', 'jewellery'],
            'ring': ['band', 'jewelry', 'finger', 'gold', 'silver', 'diamond', 'wedding', 'engagement', 'signet'],
            'necklace': ['chain', 'pendant', 'jewelry', 'choker', 'locket', 'pearls', 'beads'],
            'bracelet': ['bangle', 'wristband', 'jewelry', 'chain', 'cuff', 'charm'],
            'earring': ['stud', 'hoop', 'drop', 'jewelry', 'piercing'],
            'watch': ['smartwatch', 'timepiece', 'band', 'wrist', 'rolex', 'casio', 'apple', 'seiko', 'fossil', 'omega', 'tag', 'analog', 'digital'],
            'smartwatch': ['watch', 'tracker', 'fitbit', 'garmin', 'apple', 'samsung'],
            
            # Eyewear
            'glasses': ['sunglasses', 'spectacles', 'eyewear', 'shades', 'frames', 'reading', 'prescription', 'lenses', 'rayban', 'oakley'],
            'sunglasses': ['glasses', 'shades', 'sunnies', 'aviator', 'wayfarer', 'polarized'],
            'spectacles': ['glasses', 'specs', 'bifocals'],
            
            # Other Accessories
            'umbrella': ['parasol', 'rainshade', 'brolly', 'rain'],
            'bottle': ['flask', 'container', 'thermos', 'water', 'yeti', 'hydroflask', 'bottle', 'mug', 'cup', 'tumbler', 'shaker'],
            'keys': ['key', 'keychain', 'fob', 'remote', 'opener', 'car', 'house', 'office'],
            'hat': ['cap', 'beanie', 'headwear', 'fedora', 'bucket', 'sunhat', 'visor', 'helmet', 'baseball'],
            'belt': ['strap', 'waistband', 'leather', 'buckle', 'accessory'],
            'scarf': ['shawl', 'wrap', 'muffler', 'stole', 'hijab', 'dupatta', 'winter', 'wool', 'silk'],
            'gloves': ['mittens', 'handwear', 'winter', 'leather', 'wool', 'work'],

            # --- CLOTHING ---
            # Tops
            'shirt': ['t-shirt', 'top', 'blouse', 'tee', 'jersey', 'polo', 'button', 'flannel', 'dress', 'formal', 'casual', 'cotton', 'linen'],
            't-shirt': ['shirt', 'tee', 'top', 'crewneck', 'vneck', 'graphic'],
            'hoodie': ['jacket', 'sweatshirt', 'jumper', 'pullover', 'fleece', 'top'],
            'sweatshirt': ['hoodie', 'jumper', 'pullover', 'fleece'],
            'jacket': ['coat', 'hoodie', 'sweatshirt', 'blazer', 'outerwear', 'windbreaker', 'bomber', 'denim', 'leather', 'puffer', 'parka', 'raincoat'],
            'coat': ['jacket', 'outerwear', 'overcoat', 'trench', 'winter', 'pea'],
            'sweater': ['jumper', 'cardigan', 'pullover', 'knitwear', 'wool', 'cashmere'],
            'blazer': ['jacket', 'suit', 'formal', 'coat'],
            
            # Bottoms
            'pants': ['trousers', 'jeans', 'slacks', 'chinos', 'leggings', 'bottoms', 'joggers', 'sweatpants', 'cargos', 'shorts'],
            'jeans': ['pants', 'denim', 'trousers', 'levis', 'wrangler', 'blue', 'black', 'skinny', 'straight', 'bootcut'],
            'shorts': ['pants', 'bottoms', 'summer', 'swim', 'gym', 'cargo', 'denim'],
            'skirt': ['bottoms', 'dress', 'mini', 'midi', 'maxi', 'pencil', 'pleated'],
            
            # Footwear
            'shoe': ['sneaker', 'boot', 'sandal', 'slipper', 'footwear', 'trainer', 'jogger', 'runner', 'nike', 'adidas', 'puma', 'vans', 'converse', 'jordan', 'yeezy', 'formal', 'heels', 'flats', 'loafers'],
            'sneaker': ['shoe', 'trainer', 'nike', 'adidas', 'runner', 'tennis', 'gym', 'kicks'],
            'boot': ['shoe', 'footwear', 'winter', 'hiking', 'rain', 'timberland', 'chelsea', 'ankle', 'combat'],
            'sandal': ['shoe', 'flipflop', 'slide', 'summer', 'beach', 'crocs', 'birkenstock'],
            'heels': ['shoe', 'pumps', 'stilettos', 'wedges', 'high', 'formal'],
            
            # Dresses & Cultural
            'dress': ['gown', 'frock', 'clothing', 'outfit', 'abaya', 'burqa', 'hijab', 'niqab', 'jilbab', 'kaftan', 'robe', 'sundress', 'maxi', 'midi', 'mini', 'evening', 'formal', 'wedding', 'party', 'summer'],
            'gown': ['dress', 'formal', 'evening', 'wedding', 'ball'],
            'suit': ['formal', 'blazer', 'pants', 'tuxedo', 'business', 'jacket', 'coat'],
            'abaya': ['dress', 'gown', 'robe', 'clothing', 'burqa', 'hijab', 'niqab', 'jilbab', 'kaftan', 'islamic', 'modest'],
            'burqa': ['abaya', 'dress', 'clothing', 'islamic'],
            'hijab': ['scarf', 'headscarf', 'abaya', 'dress', 'clothing', 'islamic', 'modest'],
            'niqab': ['veil', 'face', 'abaya', 'dress', 'clothing', 'islamic'],
            'jilbab': ['coat', 'cloak', 'abaya', 'dress', 'clothing', 'islamic'],
            'kaftan': ['tunic', 'robe', 'dress', 'clothing', 'loose'],
            'robe': ['gown', 'dress', 'clothing', 'bathrobe', 'kimono', 'kaftan'],
            'saree': ['sari', 'clothing', 'indian', 'traditional', 'silk', 'cotton', 'drape'],
            'kurta': ['kameez', 'tunic', 'top', 'shirt', 'clothing', 'indian', 'traditional'],
            'kimono': ['robe', 'clothing', 'japanese', 'traditional'],
            
            # Underwear & Sleepwear
            'underwear': ['panties', 'boxers', 'briefs', 'bra', 'lingerie', 'socks', 'innerwear'],
            'socks': ['stockings', 'footwear', 'cotton', 'wool', 'ankle', 'crew'],
            'pajamas': ['sleepwear', 'pj', 'nightwear', 'nightsuit', 'loungewear'],

            # --- DOCUMENTS ---
            'document': ['file', 'folder', 'paper', 'certificate', 'form', 'report', 'contract', 'agreement', 'deed', 'record', 'statement', 'bill', 'invoice', 'receipt', 'prescription'],
            'id': ['card', 'badge', 'license', 'identification', 'passport', 'student', 'employee', 'national', 'voter', 'pan', 'aadhaar', 'driver'],
            'passport': ['id', 'document', 'travel', 'book', 'international'],
            'license': ['id', 'permit', 'card', 'driving', 'driver'],
            'visa': ['card', 'credit', 'debit', 'document', 'travel', 'permit'],
            'mastercard': ['card', 'credit', 'debit'],
            'file': ['folder', 'document', 'binder', 'portfolio', 'case'],
            'notebook': ['diary', 'journal', 'notepad', 'register', 'copybook', 'planner', 'sketchbook'],
            'diary': ['notebook', 'journal', 'notepad', 'planner'],
            'textbook': ['book', 'coursebook', 'manual', 'guide', 'study'],
            'book': ['novel', 'paperback', 'hardcover', 'textbook', 'fiction', 'nonfiction', 'story', 'literature', 'comic', 'manga'],
            'paper': ['document', 'sheet', 'printout', 'letter', 'note', 'memo'],
            'folder': ['file', 'binder', 'holder', 'organizer', 'plastic', 'envelope'],

            # --- OTHERS / HOUSEHOLD / SPORTS / ANIMALS / TOOLS ---
            # Animals
            'dog': ['puppy', 'canine', 'pet', 'animal', 'pup', 'hound', 'retriever', 'bulldog', 'poodle', 'terrier', 'beagle', 'shepherd', 'husky'],
            'puppy': ['dog', 'pet', 'animal'],
            'cat': ['kitten', 'feline', 'pet', 'animal', 'kitty', 'tabby', 'persian', 'siamese', 'maine'],
            'kitten': ['cat', 'pet', 'animal'],
            'pet': ['animal', 'dog', 'cat', 'bird', 'fish', 'hamster', 'rabbit', 'turtle'],
            'bird': ['parrot', 'pigeon', 'sparrow', 'pet', 'animal', 'cage'],
            
            # Sports
            'ball': ['football', 'soccer', 'basketball', 'tennis', 'baseball', 'cricket', 'volleyball', 'rugby', 'golf', 'pingpong'],
            'racket': ['tennis', 'badminton', 'squash', 'bat', 'paddle'],
            'bat': ['cricket', 'baseball', 'racket'],
            'helmet': ['safety', 'headgear', 'bike', 'motorcycle', 'sports'],
            'bike': ['bicycle', 'cycle', 'mountain', 'road', 'bmx', 'hybrid', 'electric', 'scooter'],
            'bicycle': ['bike', 'cycle'],
            'scooter': ['bike', 'electric', 'moped', 'vespa', 'razor'],
            'skateboard': ['board', 'skate', 'longboard', 'penny'],
            'skates': ['roller', 'inline', 'ice', 'shoes'],
            'gym': ['workout', 'fitness', 'exercise', 'equipment', 'weights', 'dumbbells', 'mat', 'bottle', 'towel', 'bag'],
            'yoga': ['mat', 'exercise', 'fitness'],
            
            # Tools
            'tool': ['hammer', 'screwdriver', 'wrench', 'drill', 'equipment', 'pliers', 'saw', 'tape', 'measure', 'knife', 'cutter', 'level'],
            'hammer': ['tool', 'mallet'],
            'drill': ['tool', 'power', 'machine'],
            'knife': ['blade', 'cutter', 'tool', 'pocket', 'swiss'],
            
            # Household
            'furniture': ['chair', 'table', 'sofa', 'couch', 'desk', 'bed', 'cabinet', 'shelf', 'stool'],
            'chair': ['seat', 'stool', 'furniture', 'office', 'dining'],
            'table': ['desk', 'furniture', 'dining', 'coffee'],
            'key': ['keys', 'house', 'car', 'lock', 'fob'],
            'lock': ['padlock', 'security', 'key'],
            'kitchen': ['utensil', 'pan', 'pot', 'knife', 'fork', 'spoon', 'plate', 'bowl', 'mug', 'cup', 'glass', 'bottle'],
            'box': ['carton', 'container', 'package', 'case', 'storage', 'crate'],
            
            # Personal Care
            'makeup': ['cosmetic', 'lipstick', 'mascara', 'foundation', 'powder', 'brush', 'palette', 'liner', 'gloss'],
            'perfume': ['fragrance', 'cologne', 'scent', 'bottle', 'spray'],
            'medicine': ['pill', 'tablet', 'drug', 'prescription', 'bottle', 'capsule', 'vitamin', 'syrup', 'inhaler'],
            'mask': ['face', 'medical', 'surgical', 'n95', 'cloth', 'covering']
        }

    def _expand_text(self, text):
        """Expand text with synonyms"""
        if not text:
            return ""
        
        # Ensure synonyms are initialized
        if not hasattr(self, 'synonyms'):
            self.synonyms = self._get_synonyms()
            
        text_lower = text.lower()
        
        # Clean punctuation to ensure words are matched correctly
        # Replace non-alphanumeric characters with space
        import re
        text_clean = re.sub(r'[^\w\s]', ' ', text_lower)
        
        words = text_clean.split()
        
        # Start with original text repeated
        expanded_terms = [text_lower]
        
        # If multiple words, also add them individually to ensure "red" and "phone" are both present
        if len(words) > 1:
             expanded_terms.extend(words)
        
        for word in words:
            # Check for direct match
            if word in self.synonyms:
                # Add synonyms but limited to top 10 to prevent dilution (increased from 5 to include more variations)
                # Double weight for first synonym (usually the most direct one)
                syns = self.synonyms[word]
                if syns:
                    expanded_terms.append(syns[0]) # Add first synonym an extra time
                    expanded_terms.extend(syns[:10])
            # Check for singular form
            elif word.endswith('s') and word[:-1] in self.synonyms:
                syns = self.synonyms[word[:-1]]
                if syns:
                    expanded_terms.append(syns[0])
                    expanded_terms.extend(syns[:10])
                
        return " ".join(expanded_terms)

    def search_similar_items(self, query, items, threshold=0.1):
        """
        Find items similar to the query using TF-IDF and Cosine Similarity
        """
        if not items:
            return []
            
        # Expand query with synonyms
        expanded_query = self._expand_text(query)
        
        # --- Use category prediction to boost context ---
        # Predict the category of the search query
        # e.g., "red phone" -> "Electronics"
        try:
            category_prediction = self.predict_category(query)
            predicted_category = category_prediction['category']
            confidence = category_prediction['confidence']
            
            # If we are confident in the category, append it to the query
            # This helps match items that are in the correct category even if keyword overlap is low
            if confidence > 0.4:
                # Append category to boost its weight (once is enough to bias ranking without excluding others)
                expanded_query += f" {predicted_category}"
        except Exception as e:
            print(f"Error predicting category for search boost: {e}")
            
        # Prepare corpus
        # Boost item name importance by repeating it 3 times
        # This ensures that a match in the name (e.g., "mobile") outweighs a match in description (e.g., "red")
        # Also include category and subcategory to ensure broad matches work (e.g. "phone" matches "Mobile" category)
        # Boost category 1x to help with broad searches like "device" -> "Electronics"
        # Reduced from 2x to avoid false positives like "bag" -> "spectacles" (both Accessories)
        item_texts = [
            f"{item['item_name']} {item['item_name']} {item['item_name']} {item.get('category', '')} {item.get('subcategory', '')} {item.get('subcategory', '')} {item['description']} {item.get('location_found', '')} {item.get('location_lost', '')}" 
            for item in items
        ]
        
        # Fit vectorizer on the combined corpus (query + items) to ensure vocabulary match
        # Ideally we'd fit on a large corpus, but for this scale, fitting on current items is fine
        # To handle query terms not in items, we fit on items + query
        
        tfidf_matrix = self.vectorizer.fit_transform(item_texts + [expanded_query])
        
        # The last vector is the query
        query_vector = tfidf_matrix[-1]
        item_vectors = tfidf_matrix[:-1]
        
        # Calculate cosine similarity
        cosine_similarities = cosine_similarity(query_vector, item_vectors).flatten()
        
        # Get maximum score to set relative threshold
        max_score = 0.0
        if len(cosine_similarities) > 0:
            max_score = np.max(cosine_similarities)
            
        # Relative threshold: either the absolute minimum threshold, 
        # or a percentage of the best match score (e.g. 1% of best match), whichever is higher
        # This filters out low-relevance items when a high-relevance item is found,
        # but keeps "okay" matches like description-only or category-only matches.
        # We use a very low percentage (1%) to ensure we don't exclude valid items just because 
        # the top result has a very high score (e.g. due to category boost)
        relative_threshold = max(threshold, max_score * 0.01)
        
        # Pair items with their scores
        results = []
        for i, score in enumerate(cosine_similarities):
            if score >= relative_threshold:
                results.append({
                    **items[i],
                    'match_score': float(score * 100)  # Convert to percentage
                })
        
        # Sort by score descending
        results.sort(key=lambda x: x['match_score'], reverse=True)
        
        return results

# Singleton instance
ml_system = LostAndFoundModel()
