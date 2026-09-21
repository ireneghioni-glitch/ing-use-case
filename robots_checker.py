"""
Robots.txt compliance checker — Marketing Spy / Belgian Banking Campaign Feature Tracker
Centralizes robots.txt content for all 5 target banks and exposes a single
`is_allowed(checkers, bank, url)` function to gate the scraping agent.
"""

from urllib.robotparser import RobotFileParser

ROBOTS_TXT = {
    "belfius": """User-agent: *
Disallow: /Avanti
Disallow: /Contest
Disallow: /wwwdexiabe/Nl/Particulier/VIADEXIA/Culture/Competitions
Disallow: /wwwdexiabe/Fr/Particulier/VIADEXIA/Culture/Competitions
Disallow: /Home_fr
Disallow: /Home_nl
Disallow: /media
Disallow: /p1
Disallow: /Style_fr
Disallow: /Style_nl
Disallow: /Styles
Disallow: /uwhuis
Disallow: /votremaison
Disallow: /Asp_lib/
Disallow: /charte/
Disallow: /charter/
Disallow: /docs/
Disallow: /NoCMS/Rates
Disallow: /NoCMS/Doccenter
Disallow: /NoCMS/Doccenter/Doc
Disallow: /NoCMS/Doccenter/fr
Disallow: /NoCMS/Doccenter/nl
Disallow: /NoCMS/Documents/papyrus
Disallow: /NoCMS/Documents/PapyrusControlTool
Disallow: /NoCMS/Documents/PapyrusControlTool/fr
Disallow: /NoCMS/Documents/PapyrusControlTool/nl
Disallow: /pdf/
Disallow: /PubliWeb-Informatif/document/
Disallow: /newsletters/
Disallow: /print/
Disallow: /PrintOnDemand/
Disallow: /nl/Common/DOSSIERS/DDNB
Disallow: /Fr/Common/DOSSIERS/DDNB
Disallow: /Private_nl
Disallow: /Private_fr
Disallow: /privatebanking/nl/nextgen/
Disallow: /privatebanking/fr/nextgen/
Disallow: /fr/newsletters
Disallow: /nl/newsletters
Disallow: /Templates
Disallow: /wwwdexiabe/Templates
Disallow: /redirect.asp?id=belfiuspulsestart_fr
Disallow: /redirect.asp?id=belfiuspulsestart_nl
Disallow: /wwwdexiabe/media/part/docu/DexiaCar_conditions_nl.pdf
Disallow: /retail/nl/mijn-belfius/
Disallow: /retail/fr/mon-belfius/
Disallow: /professional/nl/mijn-belfius/
Disallow: /professional/fr/mon-belfius/
Disallow: /retail/fr/contact/plaintes/Step2/index.aspx
Disallow: /retail/nl/contact/klachten/Step2/index.aspx
Disallow: /retail/fr/contact/plaintes/Step3/index.aspx
Disallow: /retail/nl/contact/klachten/Step3/index.aspx
Disallow: /retail/nl/producten/lenen/kredietsimulator_sea/index.aspx
Disallow: /retail/fr/produits/emprunter/simulateur-credit_sea/index.aspx
Disallow: /retail/fr/produits/emprunter/simulateur-credit_sea/index.aspx?bt_codeClientNeeds=AUTO
Disallow: /retail/nl/producten/lenen/voertuig/autolening_sea/index.aspx
Disallow: /retail/nl/producten/lenen/kredietsimulator_sea/index.aspx?bt_codeClientNeeds=AUTO
Disallow: /retail/fr/produits/emprunter/vehicule/pret-voiture_sea/index.aspx
Disallow: /retail/fr/produits/emprunter/vehicule_sea/index.aspx
Disallow: /common/NL/multimedia/MMDownloadableFile/PressReleases/2014/20140115-Autosalon.pdf
Disallow: /wwwdexiabe/media/part/docu/Prospectus_HomeCredit_NL.pdf
Disallow: /common/NL/multimedia/MMDownloadableFile/PressReleases/2014/20140218-Batibouw.pdf
Disallow: /retail/nl/producten/lenen/voertuig_sea/index.aspx
Disallow: /retail/nl/producten/lenen/voertuig/autolening-eco_sea/index.aspx
Disallow: /retail/fr/produits/emprunter/vehicule/pret-voiture-eco_sea/index.aspx
Disallow: /nocms/charte/20130313_Credit_auto_A4_CV_NL.pdf
Disallow: /retail/nl/producten/lenen/voertuig/autolening/kantoren/index.aspx
Disallow: /retail/fr/produits/emprunter/vehicule/pret-voiture/agences/index.aspx
Disallow: retail/nl/producten/verzekeringen/campagnes/2016/auto/index.aspx
Disallow: retail/fr/produits/assurance/campagnes/2016/auto/index.aspx
Disallow: wwwdexiabe/media/part/docu/DHF_Algemene_voorwaarden.pdf
Disallow: wwwdexiabe/webapplications2/apps/dexia-contest/autosalon/default.aspx
Disallow: /nl/campagnes/tempmsg/index.aspx
Disallow: /fr/campagnes/tempmsg/index.aspx
Disallow: /retail/nl/producten/lenen/voertuig/autolening/kredietsimulator_splashscreen/index.aspx
Disallow: /retail/fr/produits/emprunter/vehicule/pret-voiture/simulateur-credit_splashscreen/index.aspx
Allow: /www.dexia.be/nl/Professional/business
Allow: /www.dexia.be/fr/Professional/business
Allow: /www.dexia.be/nl/Professional/corporate
Allow: /www.dexia.be/fr/Professional/corporate
Allow: /www.dexia.be/nl/Professional/publicsocial
Allow: /www.dexia.be/fr/Professional/publicsocial
Sitemap: https://www.belfius.be/sitemap.xml""",

    "bnp_fortis": """User-agent: *
Allow: /images/favicons/
Disallow: /site/
Disallow: /images/
Disallow: /local/
Disallow: /PAPL-pr01-ws/
Disallow: /PAPL-pr01/
Disallow: /PAPL-pr02/
Disallow: /pas/
Disallow: /promo/
Disallow: /de/*
Disallow: /*.pdf
Sitemap: https://www.bnpparibasfortis.be/sitemap.xml""",

    "kbc": """User-Agent: *
Disallow: /*/$
Disallow: /site/*
Disallow: /PBL/CC028/*
Allow: /campaigns/*/$
Disallow: */aemform.iframe.html""",

    "revolut": """User-agent: *
Allow: /sitemap-*.xml*
Disallow: /api/
Disallow: */email-verification
Disallow: */help-centre
Disallow: /*.json$
Disallow: /*_buildManifest.js$
Disallow: /*_middlewareManifest.js$
Disallow: /*_ssgManifest.js$
Disallow: /*embedded
Disallow: /*/query:*
Disallow: *?*
Allow: *?amount=
Allow: *?amount-to=
Disallow: */api/*amount*
Disallow: /en-AT/money-transfer/send-money
Disallow: /en-BE/money-transfer/send-money
Disallow: /en-BG/money-transfer/send-money
Disallow: /en-BR/money-transfer/send-money
Disallow: /en-CL/money-transfer/send-money
Disallow: /en-CZ/money-transfer/send-money
Disallow: /en-DE/money-transfer/send-money
Disallow: /en-ES/money-transfer/send-money
Disallow: /en-FR/money-transfer/send-money
Disallow: /en-GR/money-transfer/send-money
Disallow: /en-HR/money-transfer/send-money
Disallow: /en-HU/money-transfer/send-money
Disallow: /en-IT/money-transfer/send-money
Disallow: /en-JP/money-transfer/send-money
Disallow: /en-LT/money-transfer/send-money
Disallow: /en-MX/money-transfer/send-money
Disallow: /en-PL/money-transfer/send-money
Disallow: /en-PT/money-transfer/send-money
Disallow: /en-RO/money-transfer/send-money
Disallow: /en-SK/money-transfer/send-money
Disallow: /en-EC/money-transfer/send-money
Disallow: /en-EE/money-transfer/send-money
Disallow: /en-AZ/money-transfer/send-money
Disallow: /en-LV/money-transfer/send-money
Disallow: */international-transfers/
Disallow: /en-ES/currency-converter/convert
Disallow: /en-BG/currency-converter/convert
Disallow: /en-CZ/currency-converter/convert
Disallow: /en-DA/currency-converter/convert
Disallow: /en-DE/currency-converter/convert
Disallow: /en-GR/currency-converter/convert
Disallow: /en-AZ/currency-converter/convert
Disallow: /en-FR/currency-converter/convert
Disallow: /en-HR/currency-converter/convert
Disallow: /en-HU/currency-converter/convert
Disallow: /en-IT/currency-converter/convert
Disallow: /en-JP/currency-converter/convert
Disallow: /en-LT/currency-converter/convert
Disallow: /en-NL/currency-converter/convert
Disallow: /en-PL/currency-converter/convert
Disallow: /en-BR/currency-converter/convert
Disallow: /en-RO/currency-converter/convert
Disallow: /en-LV/currency-converter/convert
Disallow: /en-SE/currency-converter/convert
Disallow: /en-SL/currency-converter/convert
Sitemap: https://www.revolut.com/sitemap-index.xml
Host: https://www.revolut.com""",

    "ing": """User-agent: *
Disallow: /video

Sitemap: https://www.ing.be/sitemap-cms.xml""",

    "n26": """User-agent: *
Allow: /build/**/js/*.js$

# Bad bots
User-agent: AITCSRobot/1.1
User-agent: Alexibot
User-agent: Aqua_Products
User-agent: Arachnophilia
User-agent: ASpider/0.09
User-agent: asterias
User-agent: asterias
User-agent: AURESYS/1.0
User-agent: b2w/0.1
User-agent: BackDoorBot
User-agent: BackDoorBot/1.0
User-agent: BackRub/.
User-agent: Baiduspider-video
User-agent: Big Brother
User-agent: Bizbot003
User-agent: BizBot04 kirk.overleaf.com
User-agent: Black Hole
User-agent: Black.Hole
User-agent: BlackWidow
User-agent: BLEXBot
User-agent: BlowFish
User-agent: BlowFish/1.0
User-agent: Bookmark search tool
User-agent: Bot mailto:craftbot@yahoo.com
User-agent: BotALot
User-agent: BotRightHere
User-agent: BSpider/1.0 libwww-perl/0.40
User-agent: BuiltBotTough
User-agent: Bullseye
User-agent: Bullseye/1.0
User-agent: BunnySlippers
User-agent: CACTVS Chemistry Spider
User-agent: Cegbfeieh
User-agent: ChangeDetection
User-agent: Checkbot/x.xx LWP/5.x
User-agent: CheeseBot
User-agent: CherryPicker
User-agent: CherryPickerElite/1.0
User-agent: CherryPickerSE/1.0
User-agent: ChinaClaw
User-agent: combine/0.0
User-agent: conceptbot/0.3
User-agent: Copernic
User-agent: CopyRightCheck
User-agent: cosmos
User-agent: Crescent
User-agent: Crescent Internet ToolPak HTTP OLE Control v.1.0
User-agent: Custo
User-agent: CyberPatrol SiteCat Webbot
User-agent: CyberSpyder/2.1
User-agent: Daumoa
User-agent: Deweb/1.01
User-agent: DISCo
User-agent: DISCo Pump 3.0
User-agent: DISCo Pump 3.2
User-agent: DISCoFinder
User-agent: DittoSpyder
User-agent: Download Demon
User-agent: Download Demon/3.2.0.8
User-agent: Download Demon/3.5.0.11
User-agent: dumbot
User-agent: eCatch
User-agent: eCatch/3.0
User-agent: EirGrabber
User-agent: EmailCollector
User-agent: EmailSiphon
User-agent: EmailWolf
User-agent: EnigmaBot
User-agent: EroCrawler
User-agent: es
User-agent: explorersearch
User-agent: Express WebPictures
User-agent: Express WebPictures (www.express-soft.com)
User-agent: ExtractorPro
User-agent: EyeNetIE
User-agent: FairAd Client
User-agent: FelixIDE/1.0
User-agent: fido/0.9 Harvest/1.4.pl2
User-agent: Fish-Search-Robot
User-agent: Flaming AttackBot
User-agent: FlashGet
User-agent: FlashGet WebWasher 3.2
User-agent: Foobot
User-agent: Freecrawl
User-agent: FrontPage
User-agent: FrontPage [NC,OR]
User-agent: Gaisbot
User-agent: gcreep/1.0
User-agent: GetRight
User-agent: GetRight/2.11
User-agent: GetRight/3.1
User-agent: GetRight/3.2
User-agent: GetRight/3.3
User-agent: GetRight/3.3.3
User-agent: GetRight/3.3.4
User-agent: GetRight/4.0.0
User-agent: GetRight/4.1.0
User-agent: GetRight/4.1.1
User-agent: GetRight/4.1.2
User-agent: GetRight/4.2
User-agent: GetRight/4.2b (Portuguxeas)
User-agent: GetRight/4.2c
User-agent: GetRight/4.3
User-agent: GetRight/4.5
User-agent: GetRight/4.5a
User-agent: GetRight/4.5b
User-agent: GetRight/4.5b1
User-agent: GetRight/4.5b2
User-agent: GetRight/4.5b3
User-agent: GetRight/4.5b6
User-agent: GetRight/4.5b7
User-agent: GetRight/4.5c
User-agent: GetRight/4.5d
User-agent: GetRight/4.5e
User-agent: GetRight/5.0beta1
User-agent: GetRight/5.0beta2
User-agent: GetURL.rexx v1.05
User-agent: GetWeb!
User-agent: Go!Zilla
User-agent: Go!Zilla (www.gozilla.com)
User-agent: Go!Zilla 3.3 (www.gozilla.com)
User-agent: Go!Zilla 3.5 (www.gozilla.com)
User-agent: Go-Ahead-Got-It
User-agent: Golem/1.1
User-agent: GrabNet
User-agent: Grafula
User-agent: Gromit/1.0
User-agent: grub
User-agent: HappyFunBot
User-agent: Harvest
User-agent: Harvest/1.5
User-agent: Hatena Antenna
User-agent: Hazel's Ferret Web hopper
User-agent: hloader
User-agent: HMView
User-agent: httplib
User-agent: HTTrack
User-agent: HTTrack 3.0
User-agent: HTTrack [NC,OR]
User-agent: Huaweisymantecspider
User-agent: humanlinks
User-agent: Hâ€°mâ€°hâ€°kki/0.2
User-agent: Image Stripper
User-agent: Image Sucker
User-agent: inagist.com url crawler
User-agent: IncyWincy/1.0b1
User-agent: Indy Library
User-agent: Indy Library [NC,OR]
User-agent: InfoNaviRobot
User-agent: Informant
User-agent: INGRID/0.1
User-agent: InterGET
User-agent: Internet Ninja
User-agent: Internet Ninja 4.0
User-agent: Internet Ninja 5.0
User-agent: Internet Ninja 6.0
User-agent: Iron33/1.0.2
User-agent: IsraeliSearch/1.0
User-agent: ITI Spider
User-agent: JennyBot
User-agent: JetCar
User-agent: JOC Web Spider
User-agent: JubiiRobot
User-agent: jumpstation
User-agent: Katipo/1.0
User-agent: Kenjin Spider
User-agent: Kenjin.Spider
User-agent: Keyword Density/0.9
User-agent: Keyword.Density
User-agent: KIT-Fireball/2.0 libwww/5.0a
User-agent: LabelGrab/1.1
User-agent: larbin
User-agent: larbin (samualt9@bigfoot.com)
User-agent: larbin samualt9@bigfoot.com
User-agent: larbin_2.6.2 (kabura@sushi.com)
User-agent: larbin_2.6.2 (larbin2.6.2@unspecified.mail)
User-agent: larbin_2.6.2 (listonATccDOTgatechDOTedu)
User-agent: larbin_2.6.2 (vitalbox1@hotmail.com)
User-agent: larbin_2.6.2 kabura@sushi.com
User-agent: larbin_2.6.2 larbin2.6.2@unspecified.mail
User-agent: larbin_2.6.2 larbin@correa.org
User-agent: larbin_2.6.2 listonATccDOTgatechDOTedu
User-agent: larbin_2.6.2 vitalbox1@hotmail.com
User-agent: LeechFTP
User-agent: LexiBot
User-agent: libWeb/clsHTTP
User-agent: LinkextractorPro
User-agent: linklooker
User-agent: LinkScan/8.1a Unix
User-agent: LinkScan/8.1a.Unix
User-agent: LinkWalker
User-agent: LNSpiderguy
User-agent: lwp-trivial
User-agent: lwp-trivial/1.34
User-agent: Mass Downloader
User-agent: Mass Downloader/2.2
User-agent: Mata Hari
User-agent: Mata.Hari
User-agent: MediaFox/x.y
User-agent: MerzScope
User-agent: METAGOPHER
User-agent: Microsoft URL Control
User-agent: Microsoft URL Control - 5.01.4511
User-agent: Microsoft URL Control - 6.00.8169
User-agent: Microsoft.URL
User-agent: MIDown tool
User-agent: MIIxpc
User-agent: MIIxpc/4.2
User-agent: Mister PiX
User-agent: Mister Pix II 2.01
User-agent: Mister Pix II 2.02a
User-agent: Mister PiX version.dll
User-agent: Mister.PiX
User-agent: moget
User-agent: moget/2.1
User-agent: MOMspider/1.00 libwww-perl/0.40
User-agent: Motor/0.2
User-agent: MSIECrawler
User-agent: naver
User-agent: Navroad
User-agent: NearSite
User-agent: NeoScioCrawler
User-agent: Net Vampire
User-agent: Net Vampire/3.0
User-agent: NetAnts
User-agent: NetAnts/1.10
User-agent: NetAnts/1.23
User-agent: NetAnts/1.24
User-agent: NetAnts/1.25
User-agent: NetCarta CyberPilot Pro
User-agent: NetMechanic
User-agent: NetScoop/1.0 libwww/5.0a
User-agent: NetSpider
User-agent: NetZIP
User-agent: NetZip Downloader 1.0 Win32(Nov 12 1998)
User-agent: NetZip-Downloader/1.0.62 (Win32; Dec 7 1998)
User-agent: NetZippy+(http://www.innerprise.net/usp-spider.asp)
User-agent: NHSEWalker/3.0
User-agent: NICErsPRO
User-agent: Nomad-V2.x
User-agent: NPbot
User-agent: Nutch
User-agent: Occam/1.0
User-agent: Octopus
User-agent: Offline Explorer
User-agent: Offline Explorer/1.2
User-agent: Offline Explorer/1.4
User-agent: Offline Explorer/1.6
User-agent: Offline Explorer/1.7
User-agent: Offline Explorer/1.9
User-agent: Offline Explorer/2.0
User-agent: Offline Explorer/2.1
User-agent: Offline Explorer/2.3
User-agent: Offline Explorer/2.4
User-agent: Offline Explorer/2.5
User-agent: Offline Navigator
User-agent: Offline.Explorer
User-agent: OGspider
User-agent: Open Text Site Crawler V1.0
User-agent: Openbot
User-agent: Openfind
User-agent: Openfind data gatherer
User-agent: Oracle Ultra Search
User-agent: PageGrabber
User-agent: Papa Foto
User-agent: pavuk
User-agent: pcBrowser
User-agent: PerMan
User-agent: PGP-KA/1.2
User-agent: ProPowerBot/2.14
User-agent: ProWebWalker
User-agent: psbot
User-agent: Python-urllib
User-agent: QueryN Metasearch
User-agent: QueryN.Metasearch
User-agent: R6_CommentReader
User-agent: R6_FeedFetcher
User-agent: Radiation Retriever 1.1
User-agent: RealDownload
User-agent: RealDownload/4.0.0.40
User-agent: RealDownload/4.0.0.41
User-agent: RealDownload/4.0.0.42
User-agent: ReGet
User-agent: RepoMonkey
User-agent: RepoMonkey Bait & Tackle/v1.01
User-agent: Resume Robot
User-agent: RMA
User-agent: Roverbot
User-agent: SafetyNet Robot 0.1
User-agent: searchpreview
User-agent: Senrigan/xxxxxx
User-agent: SiteSnagger
User-agent: SlySearch
User-agent: SmartDownload
User-agent: SmartDownload/1.2.76 (Win32; Apr 1 1999)
User-agent: SmartDownload/1.2.77 (Win32; Aug 17 1999)
User-agent: SmartDownload/1.2.77 (Win32; Feb 1 2000)
User-agent: SmartDownload/1.2.77 (Win32; Jun 19 2001)
User-agent: Snooper/b97_01
User-agent: Solbot/1.0 LWP/5.07
User-agent: sootle
User-agent: SpankBot
User-agent: spanner
User-agent: Spanner/1.0 (Linux 2.0.27 i586)
User-agent: spyder3.microsys.com
User-agent: Sqworm/2.9.85-BETA (beta_release; 20011115-775; i686-pc-linux
User-agent: SuperBot
User-agent: SuperBot/3.0 (Win32)
User-agent: SuperBot/3.1 (Win32)
User-agent: SuperHTTP
User-agent: SuperHTTP/1.0
User-agent: Surfbot
User-agent: suzuran
User-agent: Szukacz/1.4
User-agent: tAkeOut
User-agent: Teleport
User-agent: Teleport Pro
User-agent: Teleport Pro/1.29
User-agent: Teleport Pro/1.29.1590
User-agent: Teleport Pro/1.29.1634
User-agent: Teleport Pro/1.29.1718
User-agent: Teleport Pro/1.29.1820
User-agent: Teleport Pro/1.29.1847
User-agent: TeleportPro
User-agent: Telesoft
User-agent: The Intraformant
User-agent: The.Intraformant
User-agent: TheNomad
User-agent: TightTwatBot
User-agent: Titan
User-agent: toCrawl/UrlDispatcher
User-agent: True_Robot
User-agent: True_Robot/1.0
User-agent: turingos
User-agent: TurnitinBot
User-agent: UCSD-Crawler
User-agent: UnisterBot
User-agent: UnwindFetchor/1.0
User-agent: URL Control
User-agent: URLSpiderPro
User-agent: urlck/1.2.3
User-agent: URLy Warning
User-agent: URLy.Warning
User-agent: Valkyrie/1.0 libwww-perl/0.40
User-agent: vBSEO
User-agent: VCI
User-agent: VCI WebViewer VCI WebViewer Win32
User-agent: VoidEYE
User-agent: Web Image Collector
User-agent: Web Sucker
User-agent: Web.Image.Collector
User-agent: WebAuto
User-agent: WebAuto/3.40 (Win98; I)
User-agent: WebBandit
User-agent: WebBandit/3.50
User-agent: WebCapture 2.0
User-agent: WebCopier
User-agent: WebCopier v.2.2
User-agent: WebCopier v2.5
User-agent: WebCopier v2.6
User-agent: WebCopier v2.7a
User-agent: WebCopier v2.8
User-agent: WebCopier v3.0
User-agent: WebCopier v3.0.1
User-agent: WebCopier v3.2
User-agent: WebCopier v3.2a
User-agent: WebCopy/
User-agent: WebCrawler/3.0 Robot libwww/5.0a
User-agent: WebEMailExtrac.*
User-agent: WebEnhancer
User-agent: WebFerret
User-agent: WebFetch
User-agent: webfetch/2.1.0
User-agent: WebFetcher/0.8,
User-agent: WebGo IS
User-agent: weblayers/0.0
User-agent: WebLeacher
User-agent: WebLinker/0.0 libwww-perl/0.1
User-agent: WebmasterWorld Extractor
User-agent: WebmasterWorld Extractor
User-agent: WebmasterWorldForumBot
User-agent: WebmasterWorldForumBot
User-agent: WebMoose/0.0.0000
User-agent: WebReaper
User-agent: WebReaper [info@webreaper.net]
User-agent: WebReaper [webreaper@otway.com]
User-agent: WebReaper v9.1 - www.otway.com/webreaper
User-agent: WebReaper v9.7 - www.webreaper.net
User-agent: WebReaper v9.8 - www.webreaper.net
User-agent: WebReaper vWebReaper v7.3 - www,otway.com/webreaper
User-agent: webs@recruit.co.jp
User-agent: WebSauger
User-agent: WebSauger 1.20b
User-agent: WebSauger 1.20j
User-agent: WebSauger 1.20k
User-agent: Website eXtractor
User-agent: Website Quester
User-agent: Website Quester - www.asona.org
User-agent: Website Quester - www.esalesbiz.com/extra/
User-agent: Website.Quester
User-agent: Webster Pro
User-agent: Webster.Pro
User-agent: WebStripper
User-agent: WebStripper/2.03
User-agent: WebStripper/2.10
User-agent: WebStripper/2.12
User-agent: WebStripper/2.13
User-agent: WebStripper/2.15
User-agent: WebStripper/2.16
User-agent: WebStripper/2.19
User-agent: WebVac
User-agent: webvac/1.0
User-agent: webwalk
User-agent: WebWalker
User-agent: WebWalker/1.10
User-agent: WebWatch
User-agent: WebWhacker
User-agent: WebZIP
User-agent: WebZIP/2.75 (http://www.spidersoft.com)
User-agent: WebZIP/3.65 (http://www.spidersoft.com)
User-agent: WebZIP/3.80 (http://www.spidersoft.com)
User-agent: WebZip/4.0
User-agent: WebZIP/4.0 (http://www.spidersoft.com)
User-agent: WebZIP/4.1 (http://www.spidersoft.com)
User-agent: WebZIP/4.21
User-agent: WebZIP/4.21 (http://www.spidersoft.com)
User-agent: WebZIP/5.0
User-agent: WebZIP/5.0 (http://www.spidersoft.com)
User-agent: WebZIP/5.0 PR1 (http://www.spidersoft.com)
User-agent: Wget
User-agent: wget
User-agent: Wget/1.4.0
User-agent: Wget/1.5.2
User-agent: Wget/1.5.3
User-agent: Wget/1.6
User-agent: Wget/1.7
User-agent: Wget/1.8
User-agent: Wget/1.8.1
User-agent: Wget/1.8.1+cvs
User-agent: Wget/1.8.2
User-agent: Wget/1.9-beta
User-agent: WhoWhere Robot
User-agent: Widow
User-agent: wired-digital-newsbot/1.5
User-agent: WWW Collector
User-agent: WWW-Collector-E
User-agent: www.freeloader.com.
User-agent: WWWOFFLE
User-agent: WWWWanderer v3.0
User-agent: Xaldon WebSpider
User-agent: Xaldon WebSpider 2.5.b3
User-agent: Xaldon_WebSpider
User-agent: Xenu's
User-agent: Xenu's Link Sleuth 1.1c
User-agent: XGET/0.7
User-agent: Yasaklibot
User-agent: yes
User-agent: YesupBot
User-agent: Yeti
User-agent: Zeus
User-agent: Zeus 11389 Webster Pro V2.9 Win32
User-agent: Zeus 11652 Webster Pro V2.9 Win32
User-agent: Zeus 18018 Webster Pro V2.9 Win32
User-agent: Zeus 26378 Webster Pro V2.9 Win32
User-agent: Zeus 30747 Webster Pro V2.9 Win32
User-agent: Zeus 32297 Webster Pro V2.9 Win32
User-agent: Zeus 39206 Webster Pro V2.9 Win32
User-agent: Zeus 41641 Webster Pro V2.9 Win32
User-agent: Zeus 44238 Webster Pro V2.9 Win32
User-agent: Zeus 51070 Webster Pro V2.9 Win32
User-agent: Zeus 51674 Webster Pro V2.9 Win32
User-agent: Zeus 51837 Webster Pro V2.9 Win32
User-agent: Zeus 63567 Webster Pro V2.9 Win32
User-agent: Zeus 6694 Webster Pro V2.9 Win32
User-agent: Zeus 82016 Webster Pro V2.9 Win32
User-agent: Zeus 82900 Webster Pro V2.9 Win32
User-agent: Zeus 84842 Webster Pro V2.9 Win32
User-agent: Zeus 90872 Webster Pro V2.9 Win32
User-agent: Zeus 94934 Webster Pro V2.9 Win32
User-agent: Zeus 95245 Webster Pro V2.9 Win32
User-agent: Zeus 95351 Webster Pro V2.9 Win32
User-agent: Zeus 97371 Webster Pro V2.9 Win32
User-agent: Zeus Link Scout
User-agent: ZyBorg
Disallow: /

# Sitemaps
Sitemap: https://n26.com/sitemap-index.xml
Sitemap: https://n26.com/sitemap-blog-posts.xml
Sitemap: https://n26.com/sitemap-blog-categories.xml
Sitemap: https://n26.com/sitemap-blog-topics.xml
Sitemap: https://n26.com/sitemap-careers.xml
Sitemap: https://n26.com/sitemap-legal-documents.xml
Sitemap: https://n26.com/sitemap-pages.xml
Sitemap: https://n26.com/sitemap-videos.xml"""
}

SITEMAPS = {
    "belfius": "https://www.belfius.be/sitemap.xml",
    "bnp_fortis": "https://www.bnpparibasfortis.be/sitemap.xml",
    "kbc": "https://www.kbcbrussels.be/particuliers/fr.sitemap.xml",  # ajuster selon la langue ciblée
    "revolut": "https://www.revolut.com/sitemap-index.xml",
    "ing": "https://www.ing.be/sitemap-cms.xml",
}


def build_checkers(robots_dict: dict) -> dict:
    """Build one RobotFileParser per bank from the raw robots.txt content."""
    checkers = {}
    for bank, content in robots_dict.items():
        rp = RobotFileParser()
        rp.parse(content.splitlines())
        checkers[bank] = rp
    return checkers


def is_allowed(checkers: dict, bank: str, url: str, user_agent: str = "*") -> bool:
    """Check whether `url` may be scraped for `bank` according to its robots.txt."""
    if bank not in checkers:
        raise ValueError(f"No robots.txt loaded for bank '{bank}'. Known banks: {list(checkers)}")
    return checkers[bank].can_fetch(user_agent, url)


if __name__ == "__main__":
    checkers = build_checkers(ROBOTS_TXT)

    # Quick sanity check across all banks
    test_urls = {
        "belfius": "https://www.belfius.be/retail/fr/produits/epargner/index.aspx",
        "bnp_fortis": "https://www.bnpparibasfortis.be/promo/jeunes",
        "kbc": "https://www.kbcbrussels.be/campaigns/jeunes/fr",
        "revolut": "https://www.revolut.com/en-BE/",
        "ing": "https://www.ing.be/fr/particuliers/comptes/jeunes",
    }

    print("Compliance check results:\n")
    for bank, url in test_urls.items():
        allowed = is_allowed(checkers, bank, url)
        status = "✅ ALLOWED" if allowed else "❌ DISALLOWED"
        print(f"{status:15} {bank:12} {url}")