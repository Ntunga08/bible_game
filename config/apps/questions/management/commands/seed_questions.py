import hashlib
import random

from django.core.management.base import BaseCommand

from apps.questions.models import Category, Question


CATEGORIES = {
    'law': ('Law (Torah/Pentateuch)', 'scroll'),
    'history': ('History', 'landmark'),
    'poetry': ('Poetry & Wisdom', 'music'),
    'prophecy': ('Prophecy', 'flame'),
    'gospel': ('Gospel', 'cross'),
    'epistle': ('Epistle', 'mail'),
    'apocalyptic': ('Apocalyptic', 'sparkles'),
}


LEVEL_FACTS = {
    1: [
        ('Who built the ark?', ['Noah', 'Moses', 'David', 'Solomon'], 0, 'God told Noah to build the ark before the flood.', 'Genesis 6:14', 'old', 'law', 'recall', ['noah', 'flood'], 'Genesis'),
        ('Who led Israel out of Egypt?', ['Moses', 'Joshua', 'Samuel', 'Elijah'], 0, 'Moses led the Israelites out of Egypt by God’s command.', 'Exodus 3:10', 'old', 'law', 'recall', ['exodus', 'moses'], 'Exodus'),
        ('Who was the first man?', ['Adam', 'Abel', 'Seth', 'Cain'], 0, 'Adam was the first man formed by God.', 'Genesis 2:7', 'old', 'law', 'recall', ['creation'], 'Genesis'),
        ('Who was the mother of Jesus?', ['Mary', 'Martha', 'Ruth', 'Sarah'], 0, 'Mary was chosen to give birth to Jesus.', 'Luke 1:31', 'new', 'gospel', 'recall', ['jesus', 'mary'], 'Luke'),
        ('Where was Jesus born?', ['Bethlehem', 'Nazareth', 'Jerusalem', 'Capernaum'], 0, 'Jesus was born in Bethlehem.', 'Matthew 2:1', 'new', 'gospel', 'recall', ['birth', 'jesus'], 'Matthew'),
        ('How many disciples did Jesus choose?', ['12', '7', '10', '40'], 0, 'Jesus chose twelve apostles.', 'Luke 6:13', 'new', 'gospel', 'recall', ['disciples'], 'Luke'),
        ('Who betrayed Jesus?', ['Judas Iscariot', 'Peter', 'Thomas', 'Andrew'], 0, 'Judas Iscariot betrayed Jesus.', 'Matthew 26:14-16', 'new', 'gospel', 'recall', ['betrayal'], 'Matthew'),
        ('What did David use against Goliath?', ['A sling and stone', 'A sword', 'A spear', 'A bow'], 0, 'David struck Goliath with a stone from his sling.', '1 Samuel 17:49', 'old', 'history', 'recall', ['david', 'goliath'], '1 Samuel'),
        ('Who was swallowed by a great fish?', ['Jonah', 'Daniel', 'Elisha', 'Isaiah'], 0, 'Jonah was swallowed by a great fish after fleeing from God.', 'Jonah 1:17', 'old', 'prophecy', 'recall', ['jonah'], 'Jonah'),
        ('Who was thrown into the lions’ den?', ['Daniel', 'Joseph', 'Mordecai', 'Ezra'], 0, 'Daniel was thrown into the lions’ den for praying to God.', 'Daniel 6:16', 'old', 'prophecy', 'recall', ['daniel'], 'Daniel'),
        ('What is the first book of the Bible?', ['Genesis', 'Exodus', 'Matthew', 'Psalms'], 0, 'Genesis is the first book of the Bible.', 'Genesis 1:1', 'old', 'law', 'recall', ['bible books'], 'Genesis'),
        ('What is the last book of the Bible?', ['Revelation', 'Jude', 'Romans', 'Acts'], 0, 'Revelation is the final book of the Bible.', 'Revelation 1:1', 'new', 'apocalyptic', 'recall', ['bible books'], 'Revelation'),
        ('Who received the Ten Commandments?', ['Moses', 'Abraham', 'Isaac', 'Jacob'], 0, 'Moses received the commandments at Mount Sinai.', 'Exodus 20:1-17', 'old', 'law', 'recall', ['commandments'], 'Exodus'),
        ('Who was the strongest judge of Israel?', ['Samson', 'Gideon', 'Ehud', 'Barak'], 0, 'Samson was known for extraordinary strength.', 'Judges 16:17', 'old', 'history', 'recall', ['judges'], 'Judges'),
        ('Who denied Jesus three times?', ['Peter', 'John', 'James', 'Philip'], 0, 'Peter denied knowing Jesus three times.', 'Luke 22:61', 'new', 'gospel', 'recall', ['peter'], 'Luke'),
        ('Who baptized Jesus?', ['John the Baptist', 'Paul', 'Peter', 'James'], 0, 'John baptized Jesus in the Jordan River.', 'Matthew 3:13-17', 'new', 'gospel', 'recall', ['baptism'], 'Matthew'),
        ('What river did Israel cross into Canaan?', ['Jordan', 'Nile', 'Euphrates', 'Tigris'], 0, 'Israel crossed the Jordan River into the promised land.', 'Joshua 3:17', 'old', 'history', 'recall', ['joshua'], 'Joshua'),
        ('Who was sold by his brothers?', ['Joseph', 'Benjamin', 'Reuben', 'Judah'], 0, 'Joseph was sold by his brothers and taken to Egypt.', 'Genesis 37:28', 'old', 'law', 'recall', ['joseph'], 'Genesis'),
        ('Who climbed a tree to see Jesus?', ['Zacchaeus', 'Nicodemus', 'Bartimaeus', 'Lazarus'], 0, 'Zacchaeus climbed a sycamore tree to see Jesus.', 'Luke 19:4', 'new', 'gospel', 'recall', ['zacchaeus'], 'Luke'),
        ('Who wrote many New Testament letters?', ['Paul', 'Moses', 'David', 'Solomon'], 0, 'Paul wrote many letters to churches and believers.', 'Romans 1:1', 'new', 'epistle', 'recall', ['paul'], 'Romans'),
    ],
    2: [
        ('What sign did God give Noah after the flood?', ['Rainbow', 'Fire', 'Earthquake', 'Cloud pillar'], 0, 'The rainbow was the sign of God’s covenant with Noah.', 'Genesis 9:13', 'old', 'law', 'comprehension', ['covenant'], 'Genesis'),
        ('What plague turned Egypt’s water into blood?', ['First plague', 'Third plague', 'Seventh plague', 'Tenth plague'], 0, 'The first plague turned the Nile water into blood.', 'Exodus 7:20', 'old', 'law', 'recall', ['plagues'], 'Exodus'),
        ('Which sea did Israel cross on dry ground?', ['Red Sea', 'Dead Sea', 'Sea of Galilee', 'Mediterranean Sea'], 0, 'God parted the Red Sea for Israel.', 'Exodus 14:21-22', 'old', 'law', 'recall', ['exodus'], 'Exodus'),
        ('What food did God provide in the wilderness?', ['Manna', 'Grapes', 'Fish', 'Barley loaves'], 0, 'God provided manna from heaven.', 'Exodus 16:15', 'old', 'law', 'recall', ['provision'], 'Exodus'),
        ('Which city walls fell after Israel marched around them?', ['Jericho', 'Ai', 'Bethel', 'Hebron'], 0, 'Jericho’s walls fell after Israel obeyed God’s command.', 'Joshua 6:20', 'old', 'history', 'recall', ['jericho'], 'Joshua'),
        ('Who was Ruth’s mother-in-law?', ['Naomi', 'Hannah', 'Deborah', 'Miriam'], 0, 'Naomi was Ruth’s mother-in-law.', 'Ruth 1:16', 'old', 'history', 'recall', ['ruth'], 'Ruth'),
        ('Who anointed David as king?', ['Samuel', 'Nathan', 'Elijah', 'Elisha'], 0, 'Samuel anointed David in Bethlehem.', '1 Samuel 16:13', 'old', 'history', 'recall', ['david'], '1 Samuel'),
        ('Who asked God for wisdom?', ['Solomon', 'Saul', 'Ahab', 'Hezekiah'], 0, 'Solomon asked God for wisdom to lead Israel.', '1 Kings 3:9', 'old', 'history', 'recall', ['wisdom'], '1 Kings'),
        ('Who rebuilt Jerusalem’s wall?', ['Nehemiah', 'Ezra', 'Haggai', 'Malachi'], 0, 'Nehemiah led the rebuilding of Jerusalem’s wall.', 'Nehemiah 6:15', 'old', 'history', 'recall', ['restoration'], 'Nehemiah'),
        ('Which queen saved her people from destruction?', ['Esther', 'Vashti', 'Jezebel', 'Athaliah'], 0, 'Esther appealed to the king and helped save the Jews.', 'Esther 4:14', 'old', 'history', 'comprehension', ['esther'], 'Esther'),
        ('Who said, “The Lord is my shepherd”?', ['David', 'Moses', 'Solomon', 'Asaph'], 0, 'Psalm 23 is a psalm of David.', 'Psalm 23:1', 'old', 'poetry', 'recall', ['psalms'], 'Psalms'),
        ('What does Proverbs say is the beginning of knowledge?', ['Fear of the Lord', 'Riches', 'Long life', 'Power'], 0, 'Proverbs teaches that the fear of the Lord begins knowledge.', 'Proverbs 1:7', 'old', 'poetry', 'comprehension', ['wisdom'], 'Proverbs'),
        ('Which prophet confronted the prophets of Baal?', ['Elijah', 'Isaiah', 'Jeremiah', 'Ezekiel'], 0, 'Elijah confronted Baal’s prophets on Mount Carmel.', '1 Kings 18:21', 'old', 'prophecy', 'recall', ['elijah'], '1 Kings'),
        ('Which prophet saw dry bones live?', ['Ezekiel', 'Daniel', 'Hosea', 'Amos'], 0, 'Ezekiel saw a vision of dry bones coming to life.', 'Ezekiel 37:1-10', 'old', 'prophecy', 'recall', ['vision'], 'Ezekiel'),
        ('What did Jesus turn water into?', ['Wine', 'Oil', 'Milk', 'Honey'], 0, 'Jesus turned water into wine at Cana.', 'John 2:9', 'new', 'gospel', 'recall', ['miracles'], 'John'),
        ('Where did Jesus feed five thousand?', ['A remote place', 'Jerusalem temple', 'Nazareth synagogue', 'Caesar’s palace'], 0, 'Jesus fed the crowd in a remote place.', 'Matthew 14:15-21', 'new', 'gospel', 'recall', ['miracles'], 'Matthew'),
        ('Who was raised after four days in the tomb?', ['Lazarus', 'Jairus', 'Stephen', 'Eutychus'], 0, 'Jesus raised Lazarus from the dead.', 'John 11:43-44', 'new', 'gospel', 'recall', ['resurrection'], 'John'),
        ('Who replaced Judas among the apostles?', ['Matthias', 'Barnabas', 'Silas', 'Timothy'], 0, 'Matthias was chosen to replace Judas.', 'Acts 1:26', 'new', 'history', 'recall', ['apostles'], 'Acts'),
        ('Where were believers first called Christians?', ['Antioch', 'Jerusalem', 'Rome', 'Corinth'], 0, 'The disciples were first called Christians in Antioch.', 'Acts 11:26', 'new', 'history', 'recall', ['church'], 'Acts'),
        ('What fruit does Galatians describe?', ['Fruit of the Spirit', 'Fruit of Egypt', 'Fruit of Eden', 'Fruit of the vine'], 0, 'Galatians lists the fruit of the Spirit.', 'Galatians 5:22-23', 'new', 'epistle', 'comprehension', ['spirit'], 'Galatians'),
    ],
    3: [
        ('What covenant sign was given to Abraham?', ['Circumcision', 'Rainbow', 'Sabbath', 'Passover lamb'], 0, 'Circumcision marked God’s covenant with Abraham.', 'Genesis 17:11', 'old', 'law', 'comprehension', ['abraham', 'covenant'], 'Genesis'),
        ('What did Passover remember?', ['Deliverance from Egypt', 'Creation week', 'Temple dedication', 'Return from exile'], 0, 'Passover remembered God delivering Israel from Egypt.', 'Exodus 12:27', 'old', 'law', 'comprehension', ['passover'], 'Exodus'),
        ('Which offering expressed fellowship with God?', ['Peace offering', 'Sin offering', 'Guilt offering', 'Burnt offering only'], 0, 'Peace offerings included a shared meal of fellowship.', 'Leviticus 3:1', 'old', 'law', 'comprehension', ['offerings'], 'Leviticus'),
        ('Why did Moses lift the bronze serpent?', ['For healing after judgment', 'For military victory', 'For rain', 'For priestly ordination'], 0, 'Those who looked at the bronze serpent lived.', 'Numbers 21:8-9', 'old', 'law', 'analysis', ['wilderness'], 'Numbers'),
        ('What is the central confession of Deuteronomy 6?', ['The Lord is one', 'Wisdom is supreme', 'The king is coming', 'Zion is holy'], 0, 'The Shema declares the Lord’s uniqueness.', 'Deuteronomy 6:4', 'old', 'law', 'comprehension', ['shema'], 'Deuteronomy'),
        ('Why did Israel demand a king in Samuel’s day?', ['To be like other nations', 'To build the ark', 'To end sacrifices', 'To leave Canaan'], 0, 'Israel wanted a king like the surrounding nations.', '1 Samuel 8:5', 'old', 'history', 'analysis', ['kingdom'], '1 Samuel'),
        ('What sin did Nathan confront in David?', ['Adultery and murder', 'Idolatry at Bethel', 'Selling the birthright', 'Refusing manna'], 0, 'Nathan confronted David over Bathsheba and Uriah.', '2 Samuel 12:7-9', 'old', 'history', 'analysis', ['david'], '2 Samuel'),
        ('What divided after Solomon’s reign?', ['The kingdom of Israel', 'The priesthood', 'The tabernacle', 'The Red Sea'], 0, 'The kingdom divided into northern and southern kingdoms.', '1 Kings 12:16-20', 'old', 'history', 'analysis', ['kingdom'], '1 Kings'),
        ('What was Job’s central struggle?', ['Suffering without clear cause', 'Escaping Egypt', 'Building the temple', 'Conquering Jericho'], 0, 'Job wrestled with suffering while maintaining faith.', 'Job 1:21-22', 'old', 'poetry', 'analysis', ['suffering'], 'Job'),
        ('What does Ecclesiastes repeatedly call earthly pursuits?', ['Vanity', 'Covenant', 'Sacrifice', 'Manna'], 0, 'Ecclesiastes calls life under the sun vanity.', 'Ecclesiastes 1:2', 'old', 'poetry', 'comprehension', ['wisdom'], 'Ecclesiastes'),
        ('Which prophet promised a child called Immanuel?', ['Isaiah', 'Jeremiah', 'Ezekiel', 'Joel'], 0, 'Isaiah prophesied the sign of Immanuel.', 'Isaiah 7:14', 'old', 'prophecy', 'recall', ['messiah'], 'Isaiah'),
        ('What new covenant prophet is quoted in Hebrews 8?', ['Jeremiah', 'Obadiah', 'Nahum', 'Zephaniah'], 0, 'Hebrews quotes Jeremiah’s promise of a new covenant.', 'Jeremiah 31:31', 'old', 'prophecy', 'comprehension', ['new covenant'], 'Jeremiah'),
        ('What sign did Jonah become in Jesus’ teaching?', ['A sign of death and resurrection', 'A sign of temple taxes', 'A sign of exile length', 'A sign of Roman rule'], 0, 'Jesus connected Jonah’s three days with His own resurrection.', 'Matthew 12:40', 'both', 'gospel', 'analysis', ['jonah', 'resurrection'], 'Matthew'),
        ('What is the main theme of the Sermon on the Mount?', ['Kingdom righteousness', 'Temple measurements', 'Military conquest', 'Genealogical records'], 0, 'Jesus taught the character and righteousness of His kingdom.', 'Matthew 5:20', 'new', 'gospel', 'analysis', ['kingdom'], 'Matthew'),
        ('Why did Jesus speak in parables?', ['To reveal and conceal truth', 'To avoid Scripture', 'To replace prayer', 'To stop miracles'], 0, 'Parables revealed truth to receptive hearers and concealed it from hard hearts.', 'Matthew 13:10-17', 'new', 'gospel', 'analysis', ['parables'], 'Matthew'),
        ('What does John call Jesus in the opening chapter?', ['The Word', 'The Shepherd boy', 'The bronze serpent only', 'The tent peg'], 0, 'John identifies Jesus as the Word made flesh.', 'John 1:1,14', 'new', 'gospel', 'comprehension', ['christology'], 'John'),
        ('What event launched the public mission of the church?', ['Pentecost', 'The exile', 'The flood', 'The census'], 0, 'At Pentecost the Spirit empowered the church’s witness.', 'Acts 2:1-4', 'new', 'history', 'analysis', ['holy spirit'], 'Acts'),
        ('What is Paul’s main point in Romans 3?', ['All need righteousness through faith', 'Only Gentiles sinned', 'The law is useless', 'Rome is Jerusalem'], 0, 'Paul says all have sinned and are justified by grace through faith.', 'Romans 3:23-24', 'new', 'epistle', 'analysis', ['justification'], 'Romans'),
        ('What image does 1 Corinthians 12 use for the church?', ['One body with many members', 'One tower with many bricks', 'One boat with many sails', 'One field with many stones'], 0, 'Paul compares believers to one body with many parts.', '1 Corinthians 12:12', 'new', 'epistle', 'comprehension', ['church'], '1 Corinthians'),
        ('What does James say faith without works is?', ['Dead', 'Hidden', 'Royal', 'Finished'], 0, 'James teaches that genuine faith is shown by works.', 'James 2:17', 'new', 'epistle', 'application', ['faith', 'works'], 'James'),
    ],
    4: [
        ('How does Genesis 15 describe Abraham’s righteousness?', ['He believed the Lord', 'He conquered Canaan', 'He built the temple', 'He wrote the law'], 0, 'Abraham believed God, and it was counted as righteousness.', 'Genesis 15:6', 'old', 'law', 'analysis', ['faith'], 'Genesis'),
        ('What is the theological purpose of the tabernacle?', ['God dwelling among His people', 'A palace for Pharaoh', 'A market for merchants', 'A prison for rebels'], 0, 'The tabernacle showed God’s holy presence among Israel.', 'Exodus 25:8', 'old', 'law', 'analysis', ['tabernacle'], 'Exodus'),
        ('What does the Day of Atonement emphasize?', ['Cleansing from sin', 'Harvest celebration', 'Royal succession', 'Military training'], 0, 'Leviticus 16 focuses on atonement and cleansing.', 'Leviticus 16:30', 'old', 'law', 'analysis', ['atonement'], 'Leviticus'),
        ('Why was Moses barred from entering Canaan?', ['He dishonored God at Meribah', 'He refused circumcision', 'He ate forbidden fruit', 'He sold the birthright'], 0, 'Moses failed to uphold God as holy at Meribah.', 'Numbers 20:12', 'old', 'law', 'analysis', ['moses'], 'Numbers'),
        ('What choice does Deuteronomy set before Israel?', ['Life and death', 'Egypt and Babylon', 'Saul and David', 'Bread and fish'], 0, 'Moses calls Israel to choose life by loving and obeying God.', 'Deuteronomy 30:19', 'old', 'law', 'application', ['obedience'], 'Deuteronomy'),
        ('What pattern repeats in Judges?', ['Sin, oppression, crying out, deliverance', 'Creation, flood, exile, return', 'Birth, baptism, cross, resurrection', 'Law, psalm, proverb, prophecy'], 0, 'Judges repeatedly shows Israel falling away and God raising deliverers.', 'Judges 2:16-19', 'old', 'history', 'analysis', ['judges'], 'Judges'),
        ('What did Hannah’s prayer anticipate?', ['God reversing human fortunes', 'The fall of Jericho', 'The exile to Babylon', 'The census of Caesar'], 0, 'Hannah praises God for lifting the lowly and humbling the proud.', '1 Samuel 2:1-10', 'old', 'history', 'analysis', ['hannah'], '1 Samuel'),
        ('What promise did God make to David’s house?', ['An enduring throne', 'A rebuilt ark', 'A second exodus from Rome', 'A new mountain name'], 0, 'God promised David a lasting dynasty.', '2 Samuel 7:16', 'old', 'history', 'analysis', ['davidic covenant'], '2 Samuel'),
        ('Why did the northern kingdom fall?', ['Persistent covenant unfaithfulness', 'Lack of rainfall only', 'No written language', 'A failed census only'], 0, 'Kings explains Israel’s fall as the result of idolatry and disobedience.', '2 Kings 17:7-18', 'old', 'history', 'analysis', ['exile'], '2 Kings'),
        ('What does Psalm 2 present the Lord’s anointed as?', ['God’s installed king', 'A temple singer only', 'A Persian official', 'A wilderness scout'], 0, 'Psalm 2 depicts the Lord’s anointed king ruling the nations.', 'Psalm 2:6-8', 'old', 'poetry', 'analysis', ['messiah'], 'Psalms'),
        ('What theme dominates Isaiah 53?', ['The suffering servant bearing sin', 'Temple tax collection', 'The tower of Babel', 'The fall of Edom only'], 0, 'Isaiah 53 describes the servant suffering for others’ sins.', 'Isaiah 53:5-6', 'old', 'prophecy', 'analysis', ['servant'], 'Isaiah'),
        ('What did Jeremiah buy as a sign of hope?', ['A field', 'A crown', 'A chariot', 'A fishing net'], 0, 'Jeremiah bought a field to show future restoration.', 'Jeremiah 32:15', 'old', 'prophecy', 'analysis', ['restoration'], 'Jeremiah'),
        ('What does Ezekiel’s temple vision point toward?', ['Restored divine presence', 'Egyptian victory', 'A Roman road', 'A new famine'], 0, 'Ezekiel’s vision emphasizes restored worship and God’s presence.', 'Ezekiel 43:4-5', 'old', 'prophecy', 'analysis', ['temple'], 'Ezekiel'),
        ('What kingdom does Daniel 7 highlight?', ['An everlasting kingdom', 'A hidden garden', 'A divided priesthood', 'A merchant guild'], 0, 'Daniel sees one like a son of man receiving everlasting dominion.', 'Daniel 7:13-14', 'old', 'prophecy', 'analysis', ['kingdom'], 'Daniel'),
        ('What does Habakkuk say the righteous live by?', ['Faith', 'Wealth', 'Speed', 'Silence'], 0, 'Habakkuk says the righteous shall live by faith.', 'Habakkuk 2:4', 'old', 'prophecy', 'application', ['faith'], 'Habakkuk'),
        ('What does Jesus’ transfiguration reveal?', ['His divine glory', 'His defeat by Rome', 'His rejection of Moses', 'His need for repentance'], 0, 'The transfiguration reveals Jesus’ glory and divine sonship.', 'Matthew 17:1-5', 'new', 'gospel', 'analysis', ['glory'], 'Matthew'),
        ('What does the Last Supper connect Jesus’ death to?', ['New covenant', 'Building the ark', 'Solomon’s taxes', 'Samson’s strength'], 0, 'Jesus speaks of His blood of the covenant.', 'Luke 22:20', 'new', 'gospel', 'analysis', ['new covenant'], 'Luke'),
        ('What is the point of Romans 8:1?', ['No condemnation in Christ', 'No resurrection of bodies', 'No need for love', 'No place for prayer'], 0, 'Paul declares freedom from condemnation for those in Christ.', 'Romans 8:1', 'new', 'epistle', 'application', ['salvation'], 'Romans'),
        ('What does Ephesians say broke dividing walls?', ['Christ’s peace-making work', 'Roman law', 'Temple taxes', 'Greek philosophy'], 0, 'Christ made peace and created one new humanity.', 'Ephesians 2:14-16', 'new', 'epistle', 'analysis', ['unity'], 'Ephesians'),
        ('What does Revelation’s New Jerusalem picture?', ['God dwelling with His people forever', 'A rebuilt Babel', 'A hidden wilderness camp', 'A second Roman senate'], 0, 'Revelation pictures God dwelling with His redeemed people.', 'Revelation 21:3', 'new', 'apocalyptic', 'analysis', ['new creation'], 'Revelation'),
    ],
    5: [
        ('How does Paul use Abraham in Romans 4?', ['As an example of justification by faith', 'As proof circumcision saves by itself', 'As founder of Rome', 'As author of the Psalms'], 0, 'Paul argues Abraham was counted righteous by faith before circumcision.', 'Romans 4:9-12', 'both', 'epistle', 'analysis', ['justification'], 'Romans'),
        ('How does Hebrews interpret Melchizedek?', ['As a priestly pattern fulfilled in Christ', 'As a failed king of Egypt', 'As a Babylonian exile', 'As a Roman governor'], 0, 'Hebrews uses Melchizedek to explain Christ’s superior priesthood.', 'Hebrews 7:1-17', 'both', 'epistle', 'analysis', ['priesthood'], 'Hebrews'),
        ('What is the main contrast in Galatians 3?', ['Law and promise', 'Rome and Greece', 'Temple and synagogue buildings', 'David and Saul’s height'], 0, 'Paul contrasts the law’s role with God’s promise received by faith.', 'Galatians 3:17-22', 'new', 'epistle', 'analysis', ['law', 'promise'], 'Galatians'),
        ('How does Matthew present Jesus in relation to Moses?', ['As the authoritative teacher and deliverer', 'As rejecting all Scripture', 'As a Roman officer', 'As a temple musician'], 0, 'Matthew often frames Jesus as the greater teacher and deliverer.', 'Matthew 5:1-2', 'both', 'gospel', 'synthesis', ['moses', 'jesus'], 'Matthew'),
        ('What does John’s “I am” language emphasize?', ['Jesus’ divine identity', 'Jesus’ Roman citizenship', 'Jesus’ tribal land allotment', 'Jesus’ fishing skill'], 0, 'John’s “I am” sayings reveal Jesus’ identity and mission.', 'John 8:58', 'new', 'gospel', 'analysis', ['christology'], 'John'),
        ('What does Acts 15 decide about Gentile believers?', ['They are not required to become Jews to be saved', 'They must rebuild Jericho', 'They cannot receive the Spirit', 'They must avoid all travel'], 0, 'The Jerusalem council affirmed salvation by grace for Gentiles.', 'Acts 15:10-11', 'new', 'history', 'analysis', ['gentiles'], 'Acts'),
        ('How does 1 Peter frame Christian suffering?', ['Participation in Christ’s pattern', 'Evidence God is absent', 'A reason to abandon holiness', 'A command to seek revenge'], 0, 'Peter encourages believers to suffer faithfully as Christ did.', '1 Peter 2:21', 'new', 'epistle', 'application', ['suffering'], '1 Peter'),
        ('What does Revelation’s beast imagery call believers to?', ['Endurance and faithfulness', 'Economic ambition', 'Silence about worship', 'Return to Egypt'], 0, 'Revelation calls saints to endurance under pressure.', 'Revelation 13:10', 'new', 'apocalyptic', 'application', ['endurance'], 'Revelation'),
        ('What is the “already/not yet” tension of the kingdom?', ['God’s reign has arrived but awaits fullness', 'The kingdom ended with David', 'The kingdom is only Rome', 'The kingdom has no ethical demands'], 0, 'Jesus announces the kingdom as present while still awaiting consummation.', 'Mark 1:15', 'new', 'gospel', 'synthesis', ['kingdom'], 'Mark'),
        ('How does Isaiah’s servant theme connect to the gospel?', ['Through redemptive suffering for others', 'Through military conquest only', 'Through temple taxes', 'Through the exile never ending'], 0, 'The suffering servant provides a framework for understanding Christ’s death.', 'Isaiah 53:10-12', 'both', 'prophecy', 'synthesis', ['servant', 'cross'], 'Isaiah'),
        ('What does 2 Corinthians 5 teach about reconciliation?', ['God reconciles sinners through Christ', 'Humans reconcile God by wealth', 'Rome reconciles all nations', 'The temple veil remains closed'], 0, 'Paul says God reconciled us to Himself through Christ.', '2 Corinthians 5:18-21', 'new', 'epistle', 'analysis', ['reconciliation'], '2 Corinthians'),
        ('How does Philippians 2 describe Christ’s humility?', ['Self-emptying obedience to death', 'Avoidance of all suffering', 'Seeking imperial status', 'Refusing servant form'], 0, 'Christ humbled Himself and became obedient to death on a cross.', 'Philippians 2:5-8', 'new', 'epistle', 'analysis', ['humility'], 'Philippians'),
        ('What does Colossians say about Christ and creation?', ['All things were created through and for Him', 'He is one creature among many', 'He created only angels', 'He has no relation to creation'], 0, 'Colossians presents Christ as supreme over creation.', 'Colossians 1:16-17', 'new', 'epistle', 'analysis', ['christology'], 'Colossians'),
        ('How does James connect wisdom and conduct?', ['True wisdom shows humility and peace', 'Wisdom ignores behavior', 'Wisdom proves wealth', 'Wisdom forbids prayer'], 0, 'James says wisdom from above is pure and peaceable.', 'James 3:13-18', 'new', 'epistle', 'application', ['wisdom'], 'James'),
        ('What does 1 John use as evidence of knowing God?', ['Love and obedience', 'Secret knowledge only', 'Ancestry alone', 'Political power'], 0, 'John connects knowing God with love and obedience.', '1 John 2:3-6', 'new', 'epistle', 'application', ['love', 'obedience'], '1 John'),
        ('What does Jude urge believers to contend for?', ['The faith once delivered', 'A royal tax exemption', 'A new temple tax', 'The throne of Herod'], 0, 'Jude calls believers to contend for the faith once delivered.', 'Jude 1:3', 'new', 'epistle', 'application', ['faith'], 'Jude'),
        ('What does Daniel’s exile faithfulness model?', ['Covenant loyalty under foreign rule', 'Assimilation without limits', 'Rejection of prayer', 'Dependence on idols'], 0, 'Daniel models faithfulness while living under empire.', 'Daniel 1:8', 'old', 'prophecy', 'application', ['exile'], 'Daniel'),
        ('What does Ezra-Nehemiah show after exile?', ['Restoration with continuing spiritual need', 'Perfect obedience forever', 'The end of covenant identity', 'No need for Scripture'], 0, 'The return from exile brought restoration but also showed ongoing need for renewal.', 'Nehemiah 8:8-10', 'old', 'history', 'synthesis', ['restoration'], 'Nehemiah'),
        ('How does Psalm 110 function in New Testament theology?', ['It supports Messiah’s kingship and priesthood', 'It rejects Davidic hope', 'It describes only temple furniture', 'It names Caesar as lord'], 0, 'The New Testament uses Psalm 110 for Christ’s exalted rule and priesthood.', 'Psalm 110:1,4', 'both', 'poetry', 'synthesis', ['messiah'], 'Psalms'),
        ('What does the new creation hope unite?', ['Resurrection, judgment, and restored fellowship with God', 'Escape from creation as evil', 'Endless exile only', 'A return to Pharaoh'], 0, 'Biblical hope culminates in resurrection and renewed creation with God’s presence.', 'Revelation 21:1-5', 'both', 'apocalyptic', 'synthesis', ['new creation'], 'Revelation'),
    ],
}


class Command(BaseCommand):
    help = 'Seed manually prepared approved Bible quiz questions.'

    def handle(self, *args, **options):
        categories = self.seed_categories()
        created = 0
        updated = 0
        archived = Question.objects.filter(
            reviewer_notes='Manual seed question.',
            status='approved',
        ).update(status='archived')

        for level, facts in LEVEL_FACTS.items():
            for index, fact in enumerate(facts, start=1):
                question_data = self.build_question(level, index, fact, categories)
                _, was_created = Question.objects.update_or_create(
                    question_text=question_data['question_text'],
                    defaults=question_data,
                )
                if was_created:
                    created += 1
                else:
                    updated += 1

        self.stdout.write(
            self.style.SUCCESS(
                'Seeded questions complete. '
                f'Created: {created}. Updated: {updated}. Archived old variants: {archived}.'
            )
        )

    def seed_categories(self):
        categories = {}
        for name, (display_name, icon) in CATEGORIES.items():
            category, _ = Category.objects.update_or_create(
                name=name,
                defaults={'display_name': display_name, 'icon': icon},
            )
            categories[name] = category
        return categories

    def build_question(self, level, index, fact, categories):
        (
            question_text,
            options,
            correct_index,
            explanation,
            bible_reference,
            testament,
            category_name,
            cognitive_type,
            topic_tags,
            book_name,
        ) = fact
        shuffled_options, shuffled_correct_index = self.shuffle_options(
            options,
            correct_index,
            seed=f'{level}:{index}:{question_text}',
        )

        return {
            'question_text': f'Level {level}.{index:02d}: {question_text}',
            'options': shuffled_options,
            'correct_index': shuffled_correct_index,
            'explanation': explanation,
            'bible_reference': bible_reference,
            'full_verse_text': '',
            'difficulty': level,
            'testament': testament,
            'category': categories[category_name],
            'cognitive_type': cognitive_type,
            'topic_tags': topic_tags,
            'book_name': book_name,
            'status': 'approved',
            'quality_score': 4.5,
            'ai_generated': False,
            'generation_model': '',
            'reviewer_notes': 'Manual seed question.',
        }

    def shuffle_options(self, options, correct_index, seed):
        correct_answer = options[correct_index]
        shuffled_options = list(options)
        digest = hashlib.sha256(seed.encode('utf-8')).hexdigest()
        rng = random.Random(int(digest[:16], 16))
        rng.shuffle(shuffled_options)
        return shuffled_options, shuffled_options.index(correct_answer)
