"""ADVANCED INTEGRATED SENTINEL-RAG SYSTEM - PART 1 OF 5
Enhanced Manipulation Detection with Temporal Analysis"""
import anthropic,json,os,re,math,sqlite3,hashlib,csv,secrets,threading,statistics
from datetime import datetime,timedelta
from collections import Counter,defaultdict
from http.server import HTTPServer,BaseHTTPRequestHandler

client=anthropic.Anthropic(api_key=os.environ.get("ANTHROPIC_API_KEY"))

ADVANCED_MANIPULATION_PATTERNS={"guilt_framing":{"keywords":["after everything","ungrateful","owe me","disappointed in you","expected better","let down","sacrifice"],"phrases":[r"after (?:all|everything) (?:i|we|they)",r"you owe (?:me|us|them)",r"(?:i'm|we're) disappointed",r"expected (?:more|better) from you"],"psychological_markers":["obligation","debt","disappointment"],"intensity_multipliers":{"after everything":1.5,"ungrateful":1.3,"owe":1.4},"explanation":"Creates psychological debt and obligation through past favors","weight":1.2,"neural_impact":"high"},"emotional_urgency":{"keywords":["right now","urgent","last chance","immediately","deadline","expire","running out"],"phrases":[r"(?:right|do it) now",r"(?:last|final) (?:chance|opportunity)",r"(?:time is|we're) running out",r"expires (?:today|soon|shortly)"],"psychological_markers":["scarcity","time_pressure","fomo"],"intensity_multipliers":{"right now":1.4,"last chance":1.6,"immediately":1.3},"explanation":"Creates artificial time pressure to bypass rational decision-making","weight":1.4,"neural_impact":"critical"},"fear_appeal":{"keywords":["lose everything","disaster","ruin","catastrophe","destroy","failure","regret forever"],"phrases":[r"(?:will|you'll|could) (?:lose|regret)",r"(?:complete|total) (?:disaster|failure)",r"ruin your (?:life|future|career)",r"you'll (?:never|always) regret"],"psychological_markers":["loss_aversion","catastrophizing","threat"],"intensity_multipliers":{"lose everything":1.8,"disaster":1.5,"ruin":1.6},"explanation":"Amplifies negative outcomes beyond realistic probability","weight":1.5,"neural_impact":"critical"},"authority_pressure":{"keywords":["trust me","expert","studies show","research proves","scientists say","doctors recommend"],"phrases":[r"(?:trust|believe) me (?:i'm|i am)",r"(?:studies|research|experts) (?:show|prove|say)",r"as an? (?:expert|professional|doctor)",r"science says"],"psychological_markers":["false_authority","appeal_to_expertise","credibility_theft"],"intensity_multipliers":{"expert":1.3,"studies show":1.4,"trust me":1.2},"explanation":"Leverages false or unverified authority to bypass critical thinking","weight":1.3,"neural_impact":"high"},"gaslighting":{"keywords":["you're imagining","never happened","making it up","too sensitive","overreacting","crazy","paranoid"],"phrases":[r"(?:never|didn't) (?:happen|occur|say that)",r"you're (?:imagining|making) (?:things|it) up",r"(?:too|being) sensitive",r"you're (?:crazy|paranoid|losing it)"],"psychological_markers":["reality_denial","self_doubt","invalidation"],"intensity_multipliers":{"never happened":1.7,"imagining":1.5,"crazy":1.8},"explanation":"Denies reality to make victim question their own perception","weight":1.8,"neural_impact":"severe"},"moral_blackmail":{"keywords":["good person","should be ashamed","disappointing god","what would people think","family honor"],"phrases":[r"(?:good|decent|moral) person would",r"should be (?:ashamed|embarrassed)",r"what would (?:people|others|your (?:family|mother)) think",r"you're (?:better|bigger) than this"],"psychological_markers":["shame","moral_judgment","social_pressure"],"intensity_multipliers":{"ashamed":1.5,"good person":1.3,"disappointing":1.4},"explanation":"Weaponizes morality and social expectations to coerce behavior","weight":1.4,"neural_impact":"high"},"love_bombing":{"keywords":["nobody understands like","soulmate","meant to be","never felt this way","special connection"],"phrases":[r"(?:nobody|no one) (?:else|other) (?:understands|gets)",r"(?:we're|you're) (?:soulmates|meant to be)",r"never (?:felt|met anyone) like",r"special (?:connection|bond)"],"psychological_markers":["idealization","intensity","premature_intimacy"],"intensity_multipliers":{"soulmate":1.6,"meant to be":1.5,"special connection":1.4},"explanation":"Overwhelming positive attention to create dependency","weight":1.3,"neural_impact":"high"},"triangulation":{"keywords":["everyone else thinks","they all agree","others have said","compared to","not like"],"phrases":[r"(?:everyone|everybody|they all) (?:thinks|agrees|says)",r"compared to (?:others|them)",r"(?:not|nothing) like (?:other|normal) people",r"(?:my|his|her) ex (?:never|always)"],"psychological_markers":["comparison","peer_pressure","isolation"],"intensity_multipliers":{"everyone thinks":1.5,"compared to":1.3,"all agree":1.4},"explanation":"Uses third parties to validate position and isolate target","weight":1.3,"neural_impact":"high"},"silent_treatment":{"keywords":["fine","whatever","nothing's wrong","if you don't know","figure it out yourself"],"phrases":[r"(?:i'm )?fine\.?$",r"whatever\.?$",r"if you (?:don't know|have to ask)",r"nothing'?s? wrong",r"figure it out"],"psychological_markers":["passive_aggression","emotional_withdrawal","punishment"],"intensity_multipliers":{"if you don't know":1.5,"fine":1.2,"whatever":1.3},"explanation":"Emotional manipulation through withdrawal and vague responses","weight":1.2,"neural_impact":"medium"},"moving_goalposts":{"keywords":["not good enough","but","however","still","yet","need more"],"phrases":[r"(?:that's|it's) not (?:good )?enough",r"(?:but|however) you (?:still|also|need to)",r"(?:now|also) you (?:need|have) to",r"what about"],"psychological_markers":["impossibility","perpetual_dissatisfaction","control"],"intensity_multipliers":{"not good enough":1.6,"but":1.2,"still":1.3},"explanation":"Constantly changing requirements to maintain control","weight":1.4,"neural_impact":"high"},"false_consensus":{"keywords":["everyone knows","obviously","clearly","common sense","any reasonable person"],"phrases":[r"(?:everyone|everybody) knows",r"(?:it's )?(?:obvious|clear) that",r"(?:common|basic) sense",r"any (?:reasonable|smart|intelligent) person"],"psychological_markers":["bandwagon","peer_pressure","implicit_agreement"],"intensity_multipliers":{"everyone knows":1.5,"obviously":1.3,"common sense":1.4},"explanation":"Presents opinion as universal truth to pressure agreement","weight":1.3,"neural_impact":"medium"},"victim_playing":{"keywords":["always my fault","never appreciated","sacrifice everything","after all i've done","nobody cares"],"phrases":[r"(?:always|everything's) my fault",r"(?:never|not) appreciated",r"(?:sacrificed|gave up) everything",r"after (?:all|everything) i'?ve done",r"nobody (?:cares|understands|helps)"],"psychological_markers":["martyrdom","guilt_induction","self_pity"],"intensity_multipliers":{"after all i've done":1.6,"never appreciated":1.4,"sacrifice":1.5},"explanation":"Positions self as victim to manipulate others into compliance","weight":1.4,"neural_impact":"high"}}

ADVANCED_FALLACY_PATTERNS={"false_dilemma":{"keywords":["either","only two","must choose","no other option","black and white"],"phrases":[r"either .{1,50} or .{1,50}",r"only two (?:options|choices|ways)",r"(?:must|have to) choose between",r"no other (?:option|choice|way)"],"logical_structure":"binary_reduction","severity_factors":{"extreme_consequences":1.5,"oversimplification":1.3},"explanation":"Presents false binary choice ignoring spectrum of options","weight":1.2},"slippery_slope":{"keywords":["will lead to","eventually","next thing","opens door","where does it end"],"phrases":[r"(?:will|could|would) (?:lead|result) (?:to|in)",r"(?:eventually|ultimately|finally) .{1,50} (?:will|would)",r"(?:next|soon) (?:thing|step|you know)",r"opens (?:the )?door to",r"where (?:does|will) it (?:end|stop)"],"logical_structure":"causal_chain","severity_factors":{"catastrophic_endpoint":1.6,"no_evidence":1.4},"explanation":"Claims chain reaction of negative events without evidence","weight":1.3},"strawman":{"keywords":["so you're saying","you think","you believe","your position","you want"],"phrases":[r"so (?:you're|you are|your) saying",r"you (?:think|believe|want|claim) that",r"your (?:position|argument) is (?:that|basically)",r"(?:basically|essentially) you're (?:saying|claiming)"],"logical_structure":"misrepresentation","severity_factors":{"extreme_distortion":1.7,"intentional":1.5},"explanation":"Misrepresents opponent's argument to make it easier to attack","weight":1.4},"ad_hominem":{"keywords":["you're stupid","ignorant","idiot","moron","incompetent","uneducated","biased"],"phrases":[r"(?:you're|you are) (?:(?:an? )?(?:stupid|ignorant|idiot|moron))",r"(?:obviously|clearly) (?:biased|incompetent|uneducated)",r"what (?:would|do) you know",r"coming from (?:you|someone like you)"],"logical_structure":"personal_attack","severity_factors":{"character_assassination":1.8,"credential_attack":1.4},"explanation":"Attacks person instead of addressing their argument","weight":1.5},"hasty_generalization":{"keywords":["all","every","always","never","none","everyone","nobody"],"phrases":[r"(?:all|every) .{1,30} (?:is|are|do|have)",r"(?:always|never) .{1,30}",r"(?:everyone|everybody|nobody|no one) (?:knows|thinks|does|says)",r"without exception"],"logical_structure":"overgeneralization","severity_factors":{"absolute_language":1.5,"small_sample":1.6},"explanation":"Draws broad conclusion from insufficient evidence","weight":1.2},"circular_reasoning":{"keywords":["because","self-evident","obviously true","by definition","nature of"],"phrases":[r"(?:is|are) .{1,40} because (?:it is|it's|they are)",r"(?:self-evident|obviously true) that",r"by (?:definition|nature)",r"proves itself"],"logical_structure":"tautology","severity_factors":{"pure_circularity":1.6,"hidden_premise":1.3},"explanation":"Uses conclusion as premise creating circular logic","weight":1.3},"appeal_to_emotion":{"keywords":["think of the children","imagine","feel","heart","won't someone"],"phrases":[r"think of the (?:children|kids|families)",r"imagine (?:if|how|what)",r"(?:breaks|touches) (?:my|your|our) heart",r"won't someone (?:think|please|help)"],"logical_structure":"emotional_manipulation","severity_factors":{"exploitation":1.7,"no_logic":1.5},"explanation":"Manipulates emotions instead of using logical arguments","weight":1.4},"false_cause":{"keywords":["caused by","because of","resulted from","due to","thanks to"],"phrases":[r"(?:caused|resulted) (?:by|from)",r"because of .{1,40}",r"(?:due|thanks) to .{1,40}",r"(?:is|was) responsible for"],"logical_structure":"correlation_causation","severity_factors":{"no_mechanism":1.5,"reverse_causation":1.4},"explanation":"Assumes causation from mere correlation or sequence","weight":1.3},"appeal_to_tradition":{"keywords":["always done","tradition","ancestors","traditional","way it's always"],"phrases":[r"(?:always|traditionally) done (?:this way|it like)",r"(?:our )?(?:ancestors|forefathers|tradition)",r"(?:way|how) (?:it's|we've) always",r"(?:time-honored|age-old|ancient) (?:tradition|practice|wisdom)"],"logical_structure":"tradition_validation","severity_factors":{"no_justification":1.5,"outdated":1.4},"explanation":"Argues something is correct because it's traditional","weight":1.2},"bandwagon":{"keywords":["everyone's doing","majority","most people","popular","trending","everyone else"],"phrases":[r"(?:everyone|everybody)'?s? (?:doing|using|saying)",r"(?:the )?majority (?:of people|believes|thinks)",r"most people (?:agree|think|do|use)",r"(?:very )?popular (?:these days|now|today)",r"everyone else (?:is|does|has)"],"logical_structure":"popularity_argument","severity_factors":{"peer_pressure":1.5,"no_merit":1.4},"explanation":"Argues something is correct because many people do it","weight":1.3},"red_herring":{"keywords":["but what about","speaking of","reminds me","by the way","changing subject"],"phrases":[r"but what about .{1,40}",r"(?:speaking|talking) of .{1,40}",r"(?:reminds|makes) me (?:think of|remember)",r"by the way",r"on another note"],"logical_structure":"distraction","severity_factors":{"intentional_diversion":1.6,"relevance_loss":1.4},"explanation":"Introduces irrelevant topic to distract from main argument","weight":1.4},"no_true_scotsman":{"keywords":["no real","true","genuine","authentic","not really"],"phrases":[r"no (?:real|true|genuine) .{1,30} would",r"(?:not|isn't) (?:a )?(?:real|true|genuine|authentic)",r"(?:true|real) .{1,30} (?:wouldn't|would never)",r"that's not (?:a )?(?:real|true)"],"logical_structure":"definition_shifting","severity_factors":{"arbitrary_exclusion":1.6,"special_pleading":1.4},"explanation":"Redefines terms to exclude counterexamples","weight":1.3}}

class LinguisticFingerprint:
    FUNCTION_WORDS=['the','be','to','of','and','a','in','that','have','i','it','for','not','on','with','he','as','you','do','at','this','but','his','by','from','they','we','say','her','she','or','an','will','my','one','all','would','there','their','what','so','up','out','if','about','who','get','which','go','me']
    PASSIVE_INDICATORS=['was','were','been','being','is','are','am']
    SENTIMENT_POSITIVE=['good','great','excellent','amazing','wonderful','fantastic','love','best','perfect','beautiful','happy','joy']
    SENTIMENT_NEGATIVE=['bad','terrible','awful','horrible','worst','hate','sad','angry','poor','negative','disappointing']
    
    def extract_style_features(self,text):
        if not text or len(text.strip())<10:
            return{"error":"Text too short for analysis","total_words":0,"total_sentences":1}
        text_clean=text.strip()
        sentences=self._split_sentences(text_clean)
        words=self._tokenize(text_clean)
        words_lower=[w.lower()for w in words]
        features={}
        features['total_characters']=len(text_clean)
        features['total_words']=len(words)
        features['total_sentences']=len(sentences)
        features['avg_sentence_length']=round(len(words)/max(len(sentences),1),2)
        sentence_lengths=[len(self._tokenize(s))for s in sentences]
        features['sentence_length_variance']=round(self._calculate_variance(sentence_lengths),2)
        features['min_sentence_length']=min(sentence_lengths)if sentence_lengths else 0
        features['max_sentence_length']=max(sentence_lengths)if sentence_lengths else 0
        features['median_sentence_length']=round(statistics.median(sentence_lengths),2)if sentence_lengths else 0
        punctuation_marks=['.','!','?',',',';',':','-','—','"',"'",'(',')']
        features['punctuation_frequency']={}
        for mark in punctuation_marks:
            count=text_clean.count(mark)
            features['punctuation_frequency'][mark]=round(count/max(len(words),1)*100,2)
        features['exclamation_ratio']=round(text_clean.count('!')/max(text_clean.count('.')+text_clean.count('!'),1)*100,2)
        features['question_ratio']=round(text_clean.count('?')/max(len(sentences),1)*100,2)
        func_word_count=sum(1 for w in words_lower if w in self.FUNCTION_WORDS)
        features['function_word_ratio']=round(func_word_count/max(len(words),1)*100,2)
        features['function_word_count']=func_word_count
        features['function_word_distribution']={}
        for fw in self.FUNCTION_WORDS[:30]:
            count=words_lower.count(fw)
            if count>0:
                features['function_word_distribution'][fw]=round(count/max(len(words),1)*100,3)
        unique_words=set(words_lower)
        features['vocabulary_richness']=round(len(unique_words)/max(len(words),1),3)
        features['unique_words']=len(unique_words)
        word_freq=Counter(words_lower)
        hapax=sum(1 for count in word_freq.values()if count==1)
        dislegomena=sum(1 for count in word_freq.values()if count==2)
        features['hapax_legomena_ratio']=round(hapax/max(len(unique_words),1)*100,2)
        features['dislegomena_ratio']=round(dislegomena/max(len(unique_words),1)*100,2)
        word_lengths=[len(w)for w in words]
        features['avg_word_length']=round(sum(word_lengths)/max(len(words),1),2)
        features['min_word_length']=min(word_lengths)if word_lengths else 0
        features['max_word_length']=max(word_lengths)if word_lengths else 0
        features['median_word_length']=round(statistics.median(word_lengths),2)if word_lengths else 0
        long_words=sum(1 for w in words if len(w)>6)
        features['long_word_ratio']=round(long_words/max(len(words),1)*100,2)
        features['long_word_count']=long_words
        short_words=sum(1 for w in words if len(w)<=3)
        features['short_word_ratio']=round(short_words/max(len(words),1)*100,2)
        passive_count=sum(1 for s in sentences if any(ind in s.lower()for ind in self.PASSIVE_INDICATORS)and('by'in s.lower()or'been'in s.lower()))
        features['passive_voice_ratio']=round(passive_count/max(len(sentences),1)*100,2)
        features['passive_sentences']=passive_count
        features['active_sentences']=len(sentences)-passive_count
        syllable_count=self._estimate_syllables(words)
        features['total_syllables']=syllable_count
        features['avg_syllables_per_word']=round(syllable_count/max(len(words),1),2)
        features['flesch_reading_ease']=round(206.835-1.015*(len(words)/max(len(sentences),1))-84.6*(syllable_count/max(len(words),1)),2)
        fk_grade=0.39*(len(words)/max(len(sentences),1))+11.8*(syllable_count/max(len(words),1))-15.59
        features['flesch_kincaid_grade']=round(fk_grade,2)
        features['lexical_density']=round((len(words)-func_word_count)/max(len(words),1)*100,2)
        comma_clauses=text_clean.count(',')+text_clean.count(';')
        features['avg_clauses_per_sentence']=round((len(sentences)+comma_clauses)/max(len(sentences),1),2)
        features['total_clauses']=len(sentences)+comma_clauses
        contractions=["n't","'re","'ve","'ll","'d","'m","'s"]
        contraction_count=sum(text_clean.count(c)for c in contractions)
        features['contraction_frequency']=round(contraction_count/max(len(words),1)*100,2)
        features['contraction_count']=contraction_count
        capitalized_words=sum(1 for w in words if w[0].isupper())
        features['capitalized_word_ratio']=round(capitalized_words/max(len(words),1)*100,2)
        features['capitalized_word_count']=capitalized_words
        all_caps_words=sum(1 for w in words if w.isupper()and len(w)>1)
        features['all_caps_ratio']=round(all_caps_words/max(len(words),1)*100,2)
        positive_words=sum(1 for w in words_lower if w in self.SENTIMENT_POSITIVE)
        negative_words=sum(1 for w in words_lower if w in self.SENTIMENT_NEGATIVE)
        features['positive_word_count']=positive_words
        features['negative_word_count']=negative_words
        features['sentiment_ratio']=round((positive_words-negative_words)/max(len(words),1)*100,2)
        numbers=re.findall(r'\b\d+(?:\.\d+)?\b',text_clean)
        features['number_count']=len(numbers)
        features['number_ratio']=round(len(numbers)/max(len(words),1)*100,2)
        top_words=word_freq.most_common(10)
        features['top_10_words']=[{'word':word,'count':count}for word,count in top_words]
        features['word_frequency_distribution']=dict(word_freq.most_common(50))
        return features
    
    def _split_sentences(self,text):
        sentences=re.split(r'[.!?]+',text)
        return[s.strip()for s in sentences if s.strip()]
    
    def _tokenize(self,text):
        words=re.findall(r"\b[a-zA-Z]+(?:'[a-z]+)?\b",text)
        return[w for w in words if w]
    
    def _calculate_variance(self,values):
        if len(values)<2:
            return 0
        mean=sum(values)/len(values)
        variance=sum((x-mean)**2 for x in values)/len(values)
        return variance**0.5
    
    def _estimate_syllables(self,words):
        syllables=0
        for word in words:
            word=word.lower()
            count=len(re.findall(r'[aeiouy]+',word))
            if word.endswith('e'):
                count-=1
            syllables+=max(1,count)
        return syllables

class TemporalCache:
    def __init__(self):
        self.cache={}
    
    def get(self,key,ttl_hours):
        if key in self.cache:
            data,timestamp=self.cache[key]
            if datetime.now()-timestamp<timedelta(hours=ttl_hours):
                return data
            else:
                del self.cache[key]
        return None
    
    def set(self,key,value):
        self.cache[key]=(value,datetime.now())
    
    def clear(self):
        self.cache={}
    
    def size(self):
        return len(self.cache)

print("Part 1 loaded: Advanced patterns and base classes ready")
"""ADVANCED INTEGRATED SENTINEL-RAG SYSTEM - PART 2 OF 5
Domain Profiles, Temporal Analysis, and Enhanced Detection"""

class DomainTimeProfiles:
    profiles={"technology":{"decay_rate":0.3,"shelf_life_months":6,"update_frequency":"weekly","critical_freshness":0.7,"manipulation_sensitivity":"high","description":"Fast-moving field with frequent updates"},"medical":{"decay_rate":0.1,"shelf_life_months":24,"update_frequency":"quarterly","critical_freshness":0.6,"manipulation_sensitivity":"critical","description":"Evidence-based field with peer review cycles"},"legal":{"decay_rate":0.15,"shelf_life_months":12,"update_frequency":"monthly","critical_freshness":0.65,"manipulation_sensitivity":"high","description":"Laws and regulations change periodically"},"finance":{"decay_rate":0.8,"shelf_life_months":1,"update_frequency":"daily","critical_freshness":0.8,"manipulation_sensitivity":"critical","description":"Highly volatile with real-time changes"},"history":{"decay_rate":0.01,"shelf_life_months":1200,"update_frequency":"rarely","critical_freshness":0.3,"manipulation_sensitivity":"low","description":"Historical facts remain stable"},"science":{"decay_rate":0.12,"shelf_life_months":18,"update_frequency":"quarterly","critical_freshness":0.6,"manipulation_sensitivity":"medium","description":"Research-driven with gradual updates"},"politics":{"decay_rate":0.4,"shelf_life_months":3,"update_frequency":"weekly","critical_freshness":0.75,"manipulation_sensitivity":"critical","description":"Rapidly changing political landscape"},"news":{"decay_rate":0.9,"shelf_life_months":0.25,"update_frequency":"hourly","critical_freshness":0.9,"manipulation_sensitivity":"critical","description":"Breaking news and current events"},"general":{"decay_rate":0.2,"shelf_life_months":12,"update_frequency":"monthly","critical_freshness":0.5,"manipulation_sensitivity":"medium","description":"General knowledge domain"}}
    
    @staticmethod
    def get_profile(domain):
        return DomainTimeProfiles.profiles.get(domain.lower(),DomainTimeProfiles.profiles["general"])
    
    @staticmethod
    def get_all_domains():
        return list(DomainTimeProfiles.profiles.keys())

class TemporalEntityExtractor:
    @staticmethod
    def extract_dates(text):
        date_patterns=[r'\b\d{4}-\d{2}-\d{2}\b',r'\b\d{1,2}/\d{1,2}/\d{4}\b',r'\b(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[a-z]*\s+\d{1,2},?\s+\d{4}\b',r'\b(?:January|February|March|April|May|June|July|August|September|October|November|December)\s+\d{1,2},?\s+\d{4}\b',r'\b\d{4}\b',r'\b\d{1,2}/\d{4}\b']
        dates=[]
        for pattern in date_patterns:
            matches=re.findall(pattern,text,re.IGNORECASE)
            dates.extend(matches)
        return list(set(dates))
    
    @staticmethod
    def extract_temporal_phrases(text):
        temporal_keywords=['recently','currently','as of','since','until','latest','newest','outdated','former','previous','upcoming','now','today','yesterday','last year','this year','next year','last month','this month','last week','this week','in the past','in the future','modern','contemporary','historical','ancient','new','old','current','present']
        found_phrases=[]
        text_lower=text.lower()
        for keyword in temporal_keywords:
            if keyword in text_lower:
                found_phrases.append(keyword)
        return list(set(found_phrases))
    
    @staticmethod
    def extract_versions(text):
        version_patterns=[r'\bv?\d+\.\d+(?:\.\d+)?(?:\.\d+)?\b',r'\bversion\s+\d+(?:\.\d+)*\b',r'\brel(?:ease)?\s+\d+(?:\.\d+)*\b']
        versions=[]
        for pattern in version_patterns:
            matches=re.findall(pattern,text,re.IGNORECASE)
            versions.extend(matches)
        return list(set(versions))
    
    @staticmethod
    def extract_all_entities(text):
        return{'dates':TemporalEntityExtractor.extract_dates(text),'phrases':TemporalEntityExtractor.extract_temporal_phrases(text),'versions':TemporalEntityExtractor.extract_versions(text),'has_temporal_markers':bool(TemporalEntityExtractor.extract_dates(text)or TemporalEntityExtractor.extract_temporal_phrases(text))}

class ConfidenceDecayCalculator:
    @staticmethod
    def calculate_decay(base_confidence,months_elapsed,decay_rate):
        confidence=base_confidence*math.exp(-decay_rate*months_elapsed/12)
        return max(0.0,min(1.0,confidence))
    
    @staticmethod
    def get_freshness_score(source_date,current_date,domain="general"):
        if not source_date:
            return 0.5
        try:
            if isinstance(source_date,str):
                source_dt=datetime.fromisoformat(source_date.replace('Z',''))
            else:
                source_dt=source_date
            if isinstance(current_date,str):
                current_dt=datetime.fromisoformat(current_date.replace('Z',''))
            else:
                current_dt=current_date
            months_diff=(current_dt-source_dt).days/30.0
            profile=DomainTimeProfiles.get_profile(domain)
            decay_rate=profile["decay_rate"]
            return ConfidenceDecayCalculator.calculate_decay(1.0,months_diff,decay_rate)
        except:
            return 0.5
    
    @staticmethod
    def get_decay_analysis(source_date,domain="general"):
        current=datetime.now()
        profile=DomainTimeProfiles.get_profile(domain)
        if not source_date:
            return{'current_freshness':0.5,'status':'unknown','months_old':'unknown','shelf_life_remaining':'unknown','decay_rate':profile["decay_rate"],'critical_threshold':profile["critical_freshness"]}
        try:
            if isinstance(source_date,str):
                source_dt=datetime.fromisoformat(source_date.replace('Z',''))
            else:
                source_dt=source_date
            months_old=(current-source_dt).days/30.0
            freshness=ConfidenceDecayCalculator.calculate_decay(1.0,months_old,profile["decay_rate"])
            shelf_life=profile["shelf_life_months"]
            remaining=shelf_life-months_old
            if freshness>=profile["critical_freshness"]:
                status="current"
            elif freshness>=0.4:
                status="aging"
            else:
                status="outdated"
            return{'current_freshness':round(freshness,3),'status':status,'months_old':round(months_old,1),'shelf_life_remaining':round(remaining,1)if remaining>0 else 0,'decay_rate':profile["decay_rate"],'critical_threshold':profile["critical_freshness"]}
        except:
            return{'current_freshness':0.5,'status':'unknown','months_old':'error','shelf_life_remaining':'error','decay_rate':profile["decay_rate"],'critical_threshold':profile["critical_freshness"]}

class ConfigManager:
    def __init__(self):
        self.config={"manipulation_weight":1.0,"fallacy_weight":1.0,"high_risk_threshold":0.75,"medium_risk_threshold":0.5,"trust_score_high":80,"trust_score_moderate":60,"trust_score_low":40,"custom_patterns":{},"linguistic_weight":0.3,"temporal_weight":0.3,"manipulation_weight_advanced":1.5}
    
    def update_weights(self,m,f):
        self.config["manipulation_weight"]=m
        self.config["fallacy_weight"]=f
    
    def update_thresholds(self,h,m):
        self.config["high_risk_threshold"]=h
        self.config["medium_risk_threshold"]=m
    
    def update_advanced_weights(self,ling,temp,manip):
        self.config["linguistic_weight"]=ling
        self.config["temporal_weight"]=temp
        self.config["manipulation_weight_advanced"]=manip

config_manager=ConfigManager()

class DatabaseManager:
    def __init__(self,db="integrated_sentinel_rag.db"):
        self.db=db
        self.init_database()
    
    def init_database(self):
        c=sqlite3.connect(self.db)
        cu=c.cursor()
        cu.execute('''CREATE TABLE IF NOT EXISTS analyses (id INTEGER PRIMARY KEY AUTOINCREMENT,timestamp TEXT,text TEXT,text_hash TEXT UNIQUE,trust_score INTEGER,verdict TEXT,manipulation_type TEXT,manipulation_confidence REAL,fallacy_type TEXT,fallacy_severity TEXT,domain TEXT,freshness_score REAL,linguistic_score REAL,temporal_score REAL,full_result TEXT)''')
        cu.execute('''CREATE TABLE IF NOT EXISTS users (id INTEGER PRIMARY KEY AUTOINCREMENT,username TEXT UNIQUE,password_hash TEXT,api_key TEXT UNIQUE,created_at TEXT)''')
        cu.execute('''CREATE TABLE IF NOT EXISTS manipulation_patterns (id INTEGER PRIMARY KEY AUTOINCREMENT,pattern_name TEXT,text_sample TEXT,confidence REAL,timestamp TEXT)''')
        c.commit()
        c.close()
    
    def save_analysis(self,text,result):
        c=sqlite3.connect(self.db)
        cu=c.cursor()
        h=hashlib.md5(text.encode()).hexdigest()
        try:
            cu.execute('''INSERT INTO analyses (timestamp,text,text_hash,trust_score,verdict,manipulation_type,manipulation_confidence,fallacy_type,fallacy_severity,domain,freshness_score,linguistic_score,temporal_score,full_result) VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?)''',(result.get('timestamp',datetime.now().strftime("%Y-%m-%d %H:%M:%S")),text,h,result['trust_score']['score'],result['trust_score']['verdict'],result['manipulation_analysis']['manipulation_type'],result['manipulation_analysis']['confidence'],result['fallacy_analysis']['fallacy_type'],result['fallacy_analysis']['severity'],result.get('domain','general'),result.get('freshness_score',0.5),result.get('linguistic_score',0.5),result.get('temporal_score',0.5),json.dumps(result)))
            aid=cu.lastrowid
            c.commit()
            c.close()
            return aid
        except sqlite3.IntegrityError:
            cu.execute('SELECT id FROM analyses WHERE text_hash=?',(h,))
            row=cu.fetchone()
            c.close()
            return row[0]if row else None
        except Exception as e:
            c.close()
            print(f"Error saving analysis: {e}")
            return None
    
    def save_manipulation_pattern(self,pattern_name,text_sample,confidence):
        c=sqlite3.connect(self.db)
        cu=c.cursor()
        cu.execute('INSERT INTO manipulation_patterns (pattern_name,text_sample,confidence,timestamp) VALUES (?,?,?,?)',(pattern_name,text_sample[:200],confidence,datetime.now().isoformat()))
        c.commit()
        c.close()
    
    def get_history(self,lim=50):
        c=sqlite3.connect(self.db)
        cu=c.cursor()
        cu.execute('''SELECT id,timestamp,text,trust_score,verdict,manipulation_type,fallacy_type,freshness_score FROM analyses ORDER BY timestamp DESC LIMIT ?''',(lim,))
        r=cu.fetchall()
        c.close()
        return[{"id":x[0],"timestamp":x[1],"text":x[2][:100],"trust_score":x[3],"verdict":x[4],"manipulation":x[5],"fallacy":x[6],"freshness":x[7]}for x in r]
    
    def get_statistics(self):
        c=sqlite3.connect(self.db)
        cu=c.cursor()
        cu.execute('SELECT COUNT(*),AVG(trust_score),AVG(freshness_score) FROM analyses')
        t,a,f=cu.fetchone()
        cu.execute('SELECT manipulation_type,COUNT(*) FROM analyses GROUP BY manipulation_type')
        m=dict(cu.fetchall())
        cu.execute('SELECT fallacy_type,COUNT(*) FROM analyses GROUP BY fallacy_type')
        fa=dict(cu.fetchall())
        cu.execute('SELECT domain,COUNT(*) FROM analyses GROUP BY domain')
        d=dict(cu.fetchall())
        c.close()
        return{"total_analyses":t or 0,"average_trust_score":a or 0,"average_freshness":f or 0,"manipulation_distribution":m,"fallacy_distribution":fa,"domain_distribution":d}
    
    def create_user(self,u,p):
        c=sqlite3.connect(self.db)
        cu=c.cursor()
        ph=hashlib.sha256(p.encode()).hexdigest()
        ak=secrets.token_urlsafe(32)
        cu.execute('INSERT INTO users (username,password_hash,api_key,created_at) VALUES (?,?,?,?)',(u,ph,ak,datetime.now().isoformat()))
        c.commit()
        c.close()
        return ak
    
    def verify_api_key(self,ak):
        c=sqlite3.connect(self.db)
        cu=c.cursor()
        cu.execute('SELECT id FROM users WHERE api_key=?',(ak,))
        r=cu.fetchone()
        c.close()
        return r is not None

db_manager=DatabaseManager()

class MLEnhancer:
    def calculate_sentiment(self,t):
        pos=['good','great','excellent','love','best','amazing','wonderful','fantastic','perfect','happy','joy','brilliant','outstanding','superb']
        neg=['bad','terrible','awful','hate','worst','horrible','disappointing','poor','sad','angry','disgust','negative','failure','disaster']
        urg=['now','immediately','urgent','asap','hurry','quick','fast','deadline','expire','running out','limited time','act now']
        manip=['must','need','have to','should','ought','required','necessary','essential','critical','vital','important']
        tl=t.lower()
        w=re.findall(r'\b\w+\b',tl)
        pc=sum(1 for x in w if x in pos)
        nc=sum(1 for x in w if x in neg)
        uc=sum(1 for x in w if x in urg)
        mc=sum(1 for x in w if x in manip)
        tw=len(w)if w else 1
        return{"positive":pc/tw,"negative":nc/tw,"urgency":uc/tw,"manipulation_language":mc/tw,"neutrality":1-((pc+nc+uc+mc)/tw)}
    
    def detect_linguistic_manipulation(self,text,style_features):
        manipulation_score=0.0
        if style_features.get('exclamation_ratio',0)>20:
            manipulation_score+=0.15
        if style_features.get('all_caps_ratio',0)>5:
            manipulation_score+=0.2
        if style_features.get('question_ratio',0)>30:
            manipulation_score+=0.1
        if style_features.get('contraction_frequency',0)<2:
            manipulation_score+=0.05
        avg_sent=style_features.get('avg_sentence_length',0)
        if avg_sent<8 or avg_sent>35:
            manipulation_score+=0.1
        if style_features.get('passive_voice_ratio',0)>40:
            manipulation_score+=0.15
        return min(manipulation_score,1.0)
    
    def calculate_psychological_pressure(self,text):
        pressure_indicators={'time':['now','urgent','immediately','deadline','limited','expires','hurry','quick','fast','asap'],'obligation':['must','need','have to','should','ought','required','necessary','essential'],'authority':['expert','professional','studies','research','proven','fact','science','data'],'social':['everyone','nobody','all','most people','majority','peers','colleagues'],'emotional':['imagine','feel','think about','consider','remember','realize','understand']}
        pressure_scores={}
        tl=text.lower()
        for category,indicators in pressure_indicators.items():
            score=sum(1 for ind in indicators if ind in tl)
            pressure_scores[category]=score
        total_pressure=sum(pressure_scores.values())
        max_possible=len(text.split())*0.3
        normalized_pressure=min(total_pressure/max_possible if max_possible>0 else 0,1.0)
        return{"pressure_by_category":pressure_scores,"total_pressure_score":normalized_pressure,"pressure_level":"high"if normalized_pressure>0.5 else"medium"if normalized_pressure>0.25 else"low"}
    
    def enhance_detection(self,t,br,style_features):
        s=self.calculate_sentiment(t)
        ling_manip=self.detect_linguistic_manipulation(t,style_features)
        psych_pressure=self.calculate_psychological_pressure(t)
        er=br.copy()
        if s['urgency']>0.05 and er['manipulation_analysis']['manipulation_type']=='emotional_urgency':
            er['manipulation_analysis']['confidence']=min(0.99,er['manipulation_analysis']['confidence']*1.3)
        if s['negative']>0.1 and er['manipulation_analysis']['manipulation_type']in['fear_appeal','guilt_framing']:
            er['manipulation_analysis']['confidence']=min(0.99,er['manipulation_analysis']['confidence']*1.25)
        if s['manipulation_language']>0.08:
            er['manipulation_analysis']['confidence']=min(0.99,er['manipulation_analysis']['confidence']*1.15)
        if ling_manip>0.3:
            er['manipulation_analysis']['confidence']=min(0.99,er['manipulation_analysis']['confidence']*(1+ling_manip))
        if psych_pressure['total_pressure_score']>0.4:
            er['manipulation_analysis']['confidence']=min(0.99,er['manipulation_analysis']['confidence']*1.2)
        er['sentiment_analysis']=s
        er['linguistic_manipulation_score']=round(ling_manip,3)
        er['psychological_pressure']=psych_pressure
        er['manipulation_analysis']['enhanced']=True
        er['manipulation_analysis']['ml_adjusted']=True
        return er

ml_enhancer=MLEnhancer()

print("Part 2 loaded: Domain profiles and enhanced detection ready")
"""ADVANCED INTEGRATED SENTINEL-RAG SYSTEM - PART 3 OF 5
Core Detection Functions and Knowledge Graph"""

def detect_advanced_manipulation(text):
    tl=text.lower()
    sc={}
    ap=ADVANCED_MANIPULATION_PATTERNS.copy()
    for mt,p in ap.items():
        s=0
        m=[]
        intensity_boost=1.0
        w=p.get("weight",1.0)*config_manager.config["manipulation_weight_advanced"]
        for k in p["keywords"]:
            if k.lower()in tl:
                s+=w
                m.append(k)
                intensity_boost*=p.get("intensity_multipliers",{}).get(k,1.0)
        for pp in p["phrases"]:
            if re.search(pp,tl):
                s+=(2*w*intensity_boost)
        psych_markers=p.get("psychological_markers",[])
        psych_found=[pm for pm in psych_markers if any(word in tl for word in pm.split('_'))]
        if psych_found:
            s*=(1+len(psych_found)*0.1)
        sc[mt]={"score":s*intensity_boost,"matches":m[:5],"explanation":p["explanation"],"neural_impact":p.get("neural_impact","medium"),"psychological_markers":psych_found}
    maxt=max(sc,key=lambda k:sc[k]["score"])
    maxs=sc[maxt]["score"]
    if maxs==0:
        return{"manipulation_type":"none","confidence":0.95,"explanation":"No manipulation patterns detected.","risk_level":"low","neural_impact":"none","psychological_markers":[],"pattern_strength":0.0}
    conf=min(0.4+(maxs*0.12),0.98)
    ht=config_manager.config["high_risk_threshold"]
    mt=config_manager.config["medium_risk_threshold"]
    rl="critical"if conf>0.85 else"high"if conf>ht else"medium"if conf>mt else"low"
    pattern_strength=min(maxs/10.0,1.0)
    return{"manipulation_type":maxt,"confidence":conf,"explanation":sc[maxt]["explanation"],"indicators":sc[maxt]["matches"],"risk_level":rl,"neural_impact":sc[maxt]["neural_impact"],"psychological_markers":sc[maxt]["psychological_markers"],"pattern_strength":pattern_strength,"all_patterns_detected":{k:v["score"]for k,v in sc.items()if v["score"]>0}}

def detect_advanced_fallacy(text):
    tl=text.lower()
    sc={}
    ap=ADVANCED_FALLACY_PATTERNS.copy()
    for ft,p in ap.items():
        s=0
        w=p.get("weight",1.0)*config_manager.config["fallacy_weight"]
        for k in p["keywords"]:
            if k.lower()in tl:
                s+=w
        for pp in p["phrases"]:
            if re.search(pp,tl,re.IGNORECASE):
                s+=(2*w)
        severity_factors=p.get("severity_factors",{})
        for factor,multiplier in severity_factors.items():
            if any(word in tl for word in factor.split('_')):
                s*=multiplier
        sc[ft]={"score":s,"explanation":p["explanation"],"logical_structure":p.get("logical_structure","unknown")}
    maxt=max(sc,key=lambda k:sc[k]["score"])
    maxs=sc[maxt]["score"]
    if maxs==0:
        return{"fallacy_type":"none","explanation":"No logical fallacies detected.","severity":"none","logical_structure":"valid","fallacy_count":0}
    sev="critical"if maxs>=6 else"high"if maxs>=4 else"medium"if maxs>=2 else"low"
    fallacy_count=sum(1 for v in sc.values()if v["score"]>0)
    return{"fallacy_type":maxt,"explanation":sc[maxt]["explanation"],"severity":sev,"logical_structure":sc[maxt]["logical_structure"],"fallacy_count":fallacy_count,"all_fallacies_detected":{k:v["score"]for k,v in sc.items()if v["score"]>0}}

def analyze_claim_structure(text):
    tl=text.lower()
    structure_markers={"has_absolute":any(w in tl for w in['always','never','all','every','none','nobody','everyone']),"has_causal":any(p in tl for p in['causes','leads to','because','results in','due to','therefore']),"has_comparative":any(w in tl for w in['better','worse','best','worst','more','less','superior','inferior']),"has_normative":any(w in tl for w in['should','must','ought','need to','have to','required']),"has_conditional":any(w in tl for w in['if','unless','provided','assuming','suppose']),"has_statistical":any(w in tl for w in['percent','percentage','majority','minority','most','few','many']),"has_temporal":any(w in tl for w in['always','never','sometimes','often','rarely','usually']),"has_emotional":any(w in tl for w in['feel','believe','think','imagine','fear','hope','worry'])}
    claim_complexity=sum(structure_markers.values())
    return{**structure_markers,"claim_complexity":claim_complexity,"domain":"general"}

def generate_counter_arguments(text,ci):
    ca=[]
    if ci["has_absolute"]:
        ca.append("Absolute statements ignore nuance and exceptions. What edge cases contradict this claim?")
    if ci["has_causal"]:
        ca.append("Causation requires evidence beyond correlation. What alternative explanations exist?")
    if ci["has_comparative"]:
        ca.append("Comparisons depend on metrics and context. What criteria define 'better' here?")
    if ci["has_normative"]:
        ca.append("Normative claims require ethical justification. Why is this obligation valid?")
    if ci["has_conditional"]:
        ca.append("Conditional reasoning can hide assumptions. Are the conditions realistic?")
    if ci["has_statistical"]:
        ca.append("Statistics can be misleading. What's the sample size and methodology?")
    if ci["has_temporal"]:
        ca.append("Temporal claims need verification. Has this always been true?")
    if ci["has_emotional"]:
        ca.append("Emotional appeals can bypass logic. What's the rational argument?")
    if not ca:
        ca.append("Consider what evidence would disprove this claim.")
        ca.append("Examine the underlying assumptions and biases.")
        ca.append("Look for missing context or alternative perspectives.")
    return ca[:6]

def generate_probing_questions(ci):
    q=[]
    if ci["has_absolute"]:
        q.append("Can you identify even one exception to this absolute statement?")
    if ci["has_causal"]:
        q.append("How do we know this is causation rather than correlation?")
    if ci["has_comparative"]:
        q.append("What specific criteria make one option better than another?")
    if ci["has_normative"]:
        q.append("Why should this obligation apply to everyone?")
    if ci["has_statistical"]:
        q.append("What's the source and reliability of these statistics?")
    q.extend(["What evidence would prove this claim wrong?","Who benefits from accepting this claim?","What are the strongest arguments against this position?","What assumptions are hidden in this statement?","How might someone from a different background view this?"])
    return q[:7]

def devils_advocate(text):
    ci=analyze_claim_structure(text)
    return{"counter_arguments":generate_counter_arguments(text,ci),"probing_questions":generate_probing_questions(ci),"domain":ci["domain"],"claim_characteristics":ci,"complexity_score":ci["claim_complexity"],"critical_thinking_level":"high"if ci["claim_complexity"]>=4 else"medium"if ci["claim_complexity"]>=2 else"basic"}

def calculate_advanced_trust_score(mr,fr,freshness,ling_score,domain):
    s=100
    if mr["risk_level"]=="critical":
        s-=50
    elif mr["risk_level"]=="high":
        s-=40
    elif mr["risk_level"]=="medium":
        s-=25
    elif mr["risk_level"]=="low"and mr["manipulation_type"]!="none":
        s-=10
    neural_impact_penalty={"severe":25,"critical":20,"high":15,"medium":10,"low":5,"none":0}
    s-=neural_impact_penalty.get(mr.get("neural_impact","medium"),10)
    if fr["severity"]=="critical":
        s-=35
    elif fr["severity"]=="high":
        s-=30
    elif fr["severity"]=="medium":
        s-=20
    elif fr["severity"]=="low":
        s-=10
    fallacy_count_penalty=min(fr.get("fallacy_count",0)*5,25)
    s-=fallacy_count_penalty
    if freshness<0.3:
        s-=20
    elif freshness<0.5:
        s-=10
    elif freshness<0.7:
        s-=5
    if ling_score>0.4:
        s-=15
    elif ling_score>0.25:
        s-=10
    profile=DomainTimeProfiles.get_profile(domain)
    if profile.get("manipulation_sensitivity")=="critical":
        s*=0.9
    elif profile.get("manipulation_sensitivity")=="high":
        s*=0.95
    s=max(0,min(100,int(s)))
    ht=config_manager.config["trust_score_high"]
    mt=config_manager.config["trust_score_moderate"]
    lt=config_manager.config["trust_score_low"]
    if s>=ht:
        v="HIGH TRUST"
        c="#28a745"
        r="Text appears trustworthy and reliable."
        risk="minimal"
    elif s>=mt:
        v="MODERATE TRUST"
        c="#ffc107"
        r="Exercise caution and verify claims."
        risk="moderate"
    elif s>=lt:
        v="LOW TRUST"
        c="#fd7e14"
        r="Significant concerns detected. Critical analysis required."
        risk="high"
    else:
        v="VERY LOW TRUST"
        c="#dc3545"
        r="High risk detected. Reject or thoroughly verify."
        risk="critical"
    return{"score":s,"verdict":v,"color":c,"recommendation":r,"risk_category":risk,"score_breakdown":{"base":100,"manipulation_penalty":100-s-fallacy_count_penalty,"fallacy_penalty":fallacy_count_penalty,"freshness_impact":0 if freshness>0.7 else 10,"linguistic_impact":0 if ling_score<0.25 else 10}}

class KnowledgeGraphNode:
    def __init__(self):
        self.nodes=[]
        self.edges=[]
        self.node_counter=0
    
    def add_node(self,claim,time_ref,confidence,status,domain,metadata=None):
        node={"id":self.node_counter,"claim":claim[:150]+"..."if len(claim)>150 else claim,"time_ref":time_ref,"confidence":confidence,"status":status,"domain":domain,"timestamp":datetime.now().isoformat(),"metadata":metadata or{}}
        self.nodes.append(node)
        self.node_counter+=1
        return node["id"]
    
    def add_edge(self,from_id,to_id,relation,weight=1.0):
        edge={"from":from_id,"to":to_id,"relation":relation,"weight":weight,"created":datetime.now().isoformat()}
        self.edges.append(edge)
        return len(self.edges)-1
    
    def get_node(self,node_id):
        for node in self.nodes:
            if node["id"]==node_id:
                return node
        return None
    
    def get_related_nodes(self,node_id):
        related=[]
        for edge in self.edges:
            if edge["from"]==node_id:
                related.append(self.get_node(edge["to"]))
            elif edge["to"]==node_id:
                related.append(self.get_node(edge["from"]))
        return[n for n in related if n]
    
    def get_graph_data(self):
        return{"nodes":self.nodes,"edges":self.edges,"total_nodes":len(self.nodes),"total_edges":len(self.edges)}
    
    def get_statistics(self):
        status_counts=defaultdict(int)
        domain_counts=defaultdict(int)
        for node in self.nodes:
            status_counts[node["status"]]+=1
            domain_counts[node["domain"]]+=1
        return{"status_distribution":dict(status_counts),"domain_distribution":dict(domain_counts),"average_confidence":round(sum(n["confidence"]for n in self.nodes)/len(self.nodes),3)if self.nodes else 0}
    
    def find_manipulation_clusters(self):
        clusters=defaultdict(list)
        for node in self.nodes:
            if node.get("metadata",{}).get("manipulation_type","none")!="none":
                manip_type=node["metadata"]["manipulation_type"]
                clusters[manip_type].append(node["id"])
        return dict(clusters)

print("Part 3 loaded: Core detection and knowledge graph ready")
"""ADVANCED INTEGRATED SENTINEL-RAG SYSTEM - PART 4 OF 5
Integrated System and API Components"""

class IntegratedAdvancedSystem:
    def __init__(self):
        self.linguistic_analyzer=LinguisticFingerprint()
        self.cache=TemporalCache()
        self.knowledge_graph=KnowledgeGraphNode()
        self.analytics={"total_queries":0,"cache_hits":0,"linguistic_analyses":0,"temporal_analyses":0,"comparisons":0,"manipulations_detected":0,"fallacies_detected":0,"high_risk_detections":0}
        self.history=[]
    
    def detect_domain(self,text):
        domain_keywords={"technology":["software","app","AI","algorithm","code","programming","computer","digital","tech","data","cloud","machine learning"],"medical":["health","disease","treatment","medicine","patient","clinical","diagnosis","therapy","hospital","doctor","symptom"],"legal":["law","court","regulation","statute","legal","attorney","judge","case","contract","rights","jurisdiction"],"finance":["stock","market","price","investment","trading","financial","economy","revenue","profit","loss","dividend"],"history":["historical","century","ancient","war","revolution","empire","past","era","period","civilization"],"science":["research","study","experiment","theory","scientific","hypothesis","data","laboratory","analysis","peer review"],"politics":["election","government","policy","president","congress","vote","political","senator","legislation","democracy"],"news":["breaking","reported","announced","latest news","today","yesterday","update","developing","confirmed"]}
        text_lower=text.lower()
        domain_scores={}
        for domain,keywords in domain_keywords.items():
            score=sum(1 for keyword in keywords if keyword in text_lower)
            if score>0:
                domain_scores[domain]=score
        return max(domain_scores,key=domain_scores.get)if domain_scores else"general"
    
    def analyze_with_llm(self,text,domain):
        current_date=datetime.now().strftime("%Y-%m-%d")
        cache_key=hashlib.md5(f"{text[:200]}{domain}".encode()).hexdigest()
        cached=self.cache.get(cache_key,24)
        if cached:
            self.analytics["cache_hits"]+=1
            return cached
        prompt=f"""Analyze this text comprehensively for temporal characteristics, content quality, and potential manipulation.

Current date: {current_date}
Detected domain: {domain}
Text to analyze: {text}

Provide detailed analysis in JSON format:
{{
"time_sensitivity": true or false,
"time_reference": "specific time period mentioned or empty",
"outdated_risk": "low" or "medium" or "high" or "critical",
"confidence_score": 0.0 to 1.0,
"web_search_recommended": true or false,
"estimated_publication_date": "YYYY-MM-DD or empty",
"temporal_entities": ["list of temporal references"],
"key_topics": ["main topics discussed"],
"content_type": "factual/opinion/mixed/propaganda",
"manipulation_indicators": ["detected manipulation techniques"],
"credibility_signals": ["positive or negative credibility markers"],
"bias_indicators": ["detected biases"],
"explanation": "detailed analysis explanation",
"recommendations": ["list of recommendations"],
"domain": "{domain}",
"requires_fact_check": true or false
}}

Respond ONLY with valid JSON, no markdown formatting."""
        try:
            message=client.messages.create(model="claude-sonnet-4-20250514",max_tokens=2000,messages=[{"role":"user","content":prompt}])
            response_text=message.content[0].text.strip()
            response_text=response_text.replace("```json","").replace("```","").strip()
            result=json.loads(response_text)
            self.cache.set(cache_key,result)
            self.analytics["temporal_analyses"]+=1
            return result
        except Exception as e:
            return{"error":str(e),"time_sensitivity":False,"outdated_risk":"unknown","confidence_score":0.0,"explanation":f"Error in analysis: {str(e)}","domain":domain,"content_type":"unknown","estimated_publication_date":"","temporal_entities":[],"key_topics":[],"manipulation_indicators":[],"credibility_signals":[],"bias_indicators":[],"recommendations":[],"time_reference":"","web_search_recommended":False,"requires_fact_check":False}
    
    def comprehensive_advanced_analysis(self,text,compare_text=None):
        self.analytics["total_queries"]+=1
        domain=self.detect_domain(text)
        temporal_entities=TemporalEntityExtractor.extract_all_entities(text)
        llm_result=self.analyze_with_llm(text,domain)
        estimated_date=llm_result.get("estimated_publication_date","")
        current_date=datetime.now()
        if estimated_date:
            freshness_score=ConfidenceDecayCalculator.get_freshness_score(estimated_date,current_date,domain)
            decay_analysis=ConfidenceDecayCalculator.get_decay_analysis(estimated_date,domain)
        else:
            freshness_score=0.5
            decay_analysis=ConfidenceDecayCalculator.get_decay_analysis(None,domain)
        profile=DomainTimeProfiles.get_profile(domain)
        mr=detect_advanced_manipulation(text)
        if mr["manipulation_type"]!="none":
            self.analytics["manipulations_detected"]+=1
            db_manager.save_manipulation_pattern(mr["manipulation_type"],text,mr["confidence"])
        fr=detect_advanced_fallacy(text)
        if fr["fallacy_type"]!="none":
            self.analytics["fallacies_detected"]+=1
        dar=devils_advocate(text)
        if compare_text:
            self.analytics["comparisons"]+=1
            style_features=self.linguistic_analyzer.extract_style_features(text)
            ling_score=ml_enhancer.detect_linguistic_manipulation(text,style_features)
            linguistic_result={"style_features":style_features,"linguistic_manipulation_score":ling_score}
        else:
            self.analytics["linguistic_analyses"]+=1
            style_features=self.linguistic_analyzer.extract_style_features(text)
            ling_score=ml_enhancer.detect_linguistic_manipulation(text,style_features)
            linguistic_result={"style_features":style_features,"linguistic_manipulation_score":ling_score}
        base_result={"timestamp":datetime.now().strftime("%Y-%m-%d %H:%M:%S"),"analyzed_text":text,"manipulation_analysis":mr,"fallacy_analysis":fr,"devils_advocate_analysis":dar,"domain":domain,"freshness_score":freshness_score,"linguistic_score":ling_score,"temporal_score":freshness_score}
        enhanced_result=ml_enhancer.enhance_detection(text,base_result,style_features)
        ta=calculate_advanced_trust_score(enhanced_result["manipulation_analysis"],enhanced_result["fallacy_analysis"],freshness_score,ling_score,domain)
        enhanced_result["trust_score"]=ta
        if ta["score"]<40:
            self.analytics["high_risk_detections"]+=1
        status="current"if freshness_score>0.7 else"aging"if freshness_score>0.4 else"outdated"
        node_id=self.knowledge_graph.add_node(text,llm_result.get("time_reference","unknown"),llm_result.get("confidence_score",0.5),status,domain,{"freshness":freshness_score,"has_dates":bool(temporal_entities['dates']),"word_count":linguistic_result.get('style_features',{}).get('total_words',0),"manipulation_type":mr["manipulation_type"],"fallacy_type":fr["fallacy_type"],"trust_score":ta["score"]})
        recommendations=[]
        if ta["risk_category"]=="critical":
            recommendations.append("🚨 CRITICAL: This content shows severe manipulation. Reject immediately.")
        elif ta["risk_category"]=="high":
            recommendations.append("⚠️ HIGH RISK: Multiple red flags detected. Thorough verification essential.")
        if mr["risk_level"]in["critical","high"]:
            recommendations.append(f"🎯 Manipulation detected: {mr['manipulation_type']} ({mr['confidence']:.0%} confidence)")
        if mr.get("neural_impact")in["severe","critical"]:
            recommendations.append("🧠 ALERT: This content uses psychological manipulation techniques")
        if fr["severity"]in["critical","high"]:
            recommendations.append(f"🤔 Logical fallacy: {fr['fallacy_type']} (severity: {fr['severity']})")
        if fr.get("fallacy_count",0)>2:
            recommendations.append(f"⚡ Multiple fallacies detected ({fr['fallacy_count']} types)")
        if freshness_score<0.3:
            recommendations.append("📅 WARNING: Information likely outdated - verify with current sources")
        elif freshness_score<0.5:
            recommendations.append("⏰ Caution: Information may be dated - cross-check recent developments")
        if not temporal_entities['dates']and llm_result.get("time_sensitivity"):
            recommendations.append("🔍 Time-sensitive content lacks explicit dates")
        if llm_result.get("web_search_recommended"):
            recommendations.append("🌐 Web search recommended for latest information")
        if profile["decay_rate"]>0.5:
            recommendations.append(f"⚡ Fast-changing domain ({domain}) - information ages quickly")
        if llm_result.get("requires_fact_check"):
            recommendations.append("✓ Fact-checking strongly recommended")
        if ling_score>0.3:
            recommendations.append("📝 Linguistic analysis shows manipulative writing patterns")
        recommendations.extend(llm_result.get("recommendations",[]))
        result={"temporal_analysis":{"domain":domain,"domain_description":profile["description"],"time_sensitivity":llm_result.get("time_sensitivity",False),"outdated_risk":llm_result.get("outdated_risk","unknown"),"confidence_score":round(llm_result.get("confidence_score",0.0),3),"freshness_score":round(freshness_score,3),"freshness_indicator":"🟢 Current"if freshness_score>0.7 else"🟡 Verify"if freshness_score>0.4 else"🔴 Likely Outdated","status":status,"explanation":llm_result.get("explanation",""),"key_topics":llm_result.get("key_topics",[]),"content_type":llm_result.get("content_type","unknown"),"manipulation_indicators":llm_result.get("manipulation_indicators",[]),"credibility_signals":llm_result.get("credibility_signals",[]),"bias_indicators":llm_result.get("bias_indicators",[])},"temporal_entities":temporal_entities,"decay_analysis":decay_analysis,"domain_profile":profile,"manipulation_analysis":enhanced_result["manipulation_analysis"],"fallacy_analysis":enhanced_result["fallacy_analysis"],"devils_advocate_analysis":enhanced_result["devils_advocate_analysis"],"linguistic_analysis":linguistic_result,"sentiment_analysis":enhanced_result.get("sentiment_analysis",{}),"psychological_pressure":enhanced_result.get("psychological_pressure",{}),"trust_score":ta,"knowledge_graph_node_id":node_id,"recommendations":recommendations[:10],"metadata":{"analysis_timestamp":datetime.now().isoformat(),"text_length":len(text),"cache_used":bool(self.cache.get(hashlib.md5(f"{text[:200]}{domain}".encode()).hexdigest(),24)),"llm_enhanced":True,"ml_enhanced":True},"timestamp":datetime.now().strftime("%Y-%m-%d %H:%M:%S")}
        self.history.append({"timestamp":datetime.now().isoformat(),"domain":domain,"freshness":freshness_score,"trust_score":ta["score"],"node_id":node_id,"manipulation":mr["manipulation_type"],"fallacy":fr["fallacy_type"]})
        return result
    
    def batch_analyze(self,texts):
        results=[]
        for text in texts:
            if text and text.strip():
                result=self.comprehensive_advanced_analysis(text)
                results.append(result)
        return results
    
    def get_analytics(self):
        return self.analytics
    
    def get_knowledge_graph(self):
        return self.knowledge_graph.get_graph_data()
    
    def get_graph_statistics(self):
        stats=self.knowledge_graph.get_statistics()
        stats["manipulation_clusters"]=self.knowledge_graph.find_manipulation_clusters()
        return stats
    
    def get_history(self):
        return self.history
    
    def clear_cache(self):
        self.cache.clear()
        return"Cache cleared successfully"

class IntegratedAPIHandler(BaseHTTPRequestHandler):
    system=None
    
    def do_POST(self):
        if self.path=='/api/analyze':
            cl=int(self.headers.get('Content-Length',0))
            bd=self.rfile.read(cl).decode('utf-8')
            data=json.loads(bd)
            ak=self.headers.get('X-API-Key','')
            if not db_manager.verify_api_key(ak):
                self.send_response(401)
                self.end_headers()
                self.wfile.write(json.dumps({"error":"Invalid API key"}).encode())
                return
            text=data.get('text','')
            if not text:
                self.send_response(400)
                self.end_headers()
                self.wfile.write(json.dumps({"error":"No text provided"}).encode())
                return
            result=self.system.comprehensive_advanced_analysis(text)
            db_manager.save_analysis(text,result)
            self.send_response(200)
            self.send_header('Content-type','application/json')
            self.end_headers()
            self.wfile.write(json.dumps(result).encode())
        elif self.path=='/api/batch':
            cl=int(self.headers.get('Content-Length',0))
            bd=self.rfile.read(cl).decode('utf-8')
            data=json.loads(bd)
            ak=self.headers.get('X-API-Key','')
            if not db_manager.verify_api_key(ak):
                self.send_response(401)
                self.end_headers()
                self.wfile.write(json.dumps({"error":"Invalid API key"}).encode())
                return
            texts=data.get('texts',[])
            if not texts:
                self.send_response(400)
                self.end_headers()
                self.wfile.write(json.dumps({"error":"No texts provided"}).encode())
                return
            results=self.system.batch_analyze(texts)
            self.send_response(200)
            self.send_header('Content-type','application/json')
            self.end_headers()
            self.wfile.write(json.dumps({"results":results,"count":len(results)}).encode())
        elif self.path=='/api/stats':
            ak=self.headers.get('X-API-Key','')
            if not db_manager.verify_api_key(ak):
                self.send_response(401)
                self.end_headers()
                self.wfile.write(json.dumps({"error":"Invalid API key"}).encode())
                return
            stats=db_manager.get_statistics()
            self.send_response(200)
            self.send_header('Content-type','application/json')
            self.end_headers()
            self.wfile.write(json.dumps(stats).encode())
        else:
            self.send_response(404)
            self.end_headers()
    
    def log_message(self,format,*args):
        pass

def start_integrated_api_server(system,port=8080):
    IntegratedAPIHandler.system=system
    server=HTTPServer(('localhost',port),IntegratedAPIHandler)
    print(f"🚀 Integrated API Server running on http://localhost:{port}")
    print(f"Endpoints: /api/analyze, /api/batch, /api/stats")
    server.serve_forever()

def generate_advanced_html_report(analysis):
    text=analysis.get("analyzed_text","")
    manip=analysis["manipulation_analysis"]
    fallacy=analysis["fallacy_analysis"]
    devils_adv=analysis["devils_advocate_analysis"]
    trust=analysis["trust_score"]
    temporal=analysis["temporal_analysis"]
    timestamp=analysis.get("timestamp","")
    sentiment=analysis.get("sentiment_analysis",{})
    pressure=analysis.get("psychological_pressure",{})
    counter_args_html="".join([f"<li><strong>Point {i}:</strong> {arg}</li>"for i,arg in enumerate(devils_adv["counter_arguments"],1)])
    questions_html="".join([f"<li><strong>Q{i}:</strong> {q}</li>"for i,q in enumerate(devils_adv["probing_questions"],1)])
    indicators_html="".join([f'<span class="badge">"{ind}"</span> 'for ind in manip.get("indicators",[])[:5]])
    recommendations_html="".join([f"<li>{rec}</li>"for rec in analysis.get("recommendations",[])])
    html_content=f'''<!DOCTYPE html><html><head><meta charset="UTF-8"><title>Advanced Integrated Analysis Report</title><style>*{{margin:0;padding:0;box-sizing:border-box}}body{{font-family:system-ui;background:linear-gradient(135deg,#667eea,#764ba2);padding:20px;min-height:100vh}}.container{{max-width:1400px;margin:0 auto;background:white;border-radius:20px;box-shadow:0 20px 60px rgba(0,0,0,0.3);overflow:hidden}}.header{{background:linear-gradient(135deg,#1e3c72,#2a5298);color:white;padding:40px;text-align:center}}.header h1{{font-size:48px;margin-bottom:10px}}.trust-score{{background:{trust['color']};color:white;padding:40px;text-align:center}}.trust-score .score{{font-size:80px;font-weight:bold;margin-bottom:10px}}.trust-score .verdict{{font-size:36px;font-weight:bold;letter-spacing:3px;margin-bottom:15px}}.trust-score .recommendation{{font-size:20px;opacity:0.95}}.content{{padding:40px}}.section{{margin-bottom:40px}}.section-title{{font-size:30px;color:#1e3c72;margin-bottom:20px;padding-bottom:10px;border-bottom:3px solid #667eea}}.text-box{{background:linear-gradient(135deg,#667eea,#764ba2);color:white;padding:30px;border-radius:15px;font-size:18px;line-height:1.8;font-style:italic;box-shadow:0 4px 15px rgba(0,0,0,0.2)}}.analysis-card{{background:#f8f9fa;border-radius:12px;padding:25px;margin-bottom:20px;border-left:5px solid #667eea;box-shadow:0 2px 10px rgba(0,0,0,0.1)}}.analysis-card h3{{color:#1e3c72;font-size:24px;margin-bottom:15px}}.analysis-card .result{{font-size:26px;font-weight:bold;color:#667eea;margin-bottom:10px;text-transform:uppercase}}.analysis-card .explanation{{color:#555;line-height:1.7;margin-top:10px}}.badge{{display:inline-block;background:#667eea;color:white;padding:5px 12px;border-radius:20px;font-size:13px;margin:5px 5px 5px 0}}.risk-indicator{{display:inline-block;padding:8px 20px;border-radius:25px;font-weight:bold;font-size:14px;text-transform:uppercase;letter-spacing:1px}}.risk-critical{{background:#8b0000;color:white}}.risk-high{{background:#dc3545;color:white}}.risk-medium{{background:#ffc107;color:#333}}.risk-low{{background:#28a745;color:white}}ul{{list-style:none;padding:0}}li{{background:white;padding:15px;margin-bottom:12px;border-radius:8px;border-left:4px solid #667eea;line-height:1.7;box-shadow:0 2px 5px rgba(0,0,0,0.1)}}li strong{{color:#1e3c72}}.meta-info{{background:#e3f2fd;padding:15px;border-radius:8px;margin-top:30px;text-align:center;color:#1976D2;font-size:14px}}.footer{{background:#f8f9fa;padding:30px;text-align:center;color:#6c757d;border-top:1px solid #dee2e6}}.stats-grid{{display:grid;grid-template-columns:repeat(auto-fit,minmax(250px,1fr));gap:15px;margin-top:15px}}.stat-box{{background:white;padding:15px;border-radius:8px;box-shadow:0 2px 5px rgba(0,0,0,0.1)}}.stat-label{{font-size:12px;color:#666;text-transform:uppercase}}.stat-value{{font-size:24px;font-weight:bold;color:#667eea;margin-top:5px}}</style></head><body><div class="container"><div class="header"><h1>🛡️ ADVANCED INTEGRATED ANALYSIS</h1><div>Sentinel-RAG System • Comprehensive Critical Thinking Analysis</div></div><div class="trust-score"><div class="score">{trust['score']}/100</div><div class="verdict">{trust['verdict']}</div><div class="recommendation">{trust['recommendation']}</div><div style="margin-top:15px;font-size:18px;">Risk Category: {trust['risk_category'].upper()}</div></div><div class="content"><div class="section"><div class="section-title">📋 Analyzed Text</div><div class="text-box">{text}</div></div><div class="section"><div class="section-title">🔍 Module 1: Advanced Manipulation Detection</div><div class="analysis-card"><h3>Detection Result</h3><div class="result">{manip['manipulation_type']}</div><div class="risk-indicator risk-{manip['risk_level']}">Risk: {manip['risk_level'].upper()}</div><div class="explanation">{manip['explanation']}</div>'''
    if indicators_html:
        html_content+=f'<div style="margin-top:15px;"><strong>Indicators:</strong><br>{indicators_html}</div>'
    html_content+=f'''<div class="stats-grid"><div class="stat-box"><div class="stat-label">Confidence</div><div class="stat-value">{manip['confidence']:.0%}</div></div><div class="stat-box"><div class="stat-label">Neural Impact</div><div class="stat-value">{manip.get('neural_impact','N/A').upper()}</div></div><div class="stat-box"><div class="stat-label">Pattern Strength</div><div class="stat-value">{manip.get('pattern_strength',0):.1%}</div></div></div></div></div><div class="section"><div class="section-title">🧠 Module 2: Advanced Fallacy Detection</div><div class="analysis-card"><h3>Logical Analysis</h3><div class="result">{fallacy['fallacy_type']}</div><div class="risk-indicator risk-{fallacy['severity']}">Severity: {fallacy['severity'].upper()}</div><div class="explanation">{fallacy['explanation']}</div><div class="stats-grid"><div class="stat-box"><div class="stat-label">Fallacy Count</div><div class="stat-value">{fallacy.get('fallacy_count',0)}</div></div><div class="stat-box"><div class="stat-label">Logical Structure</div><div class="stat-value">{fallacy.get('logical_structure','N/A').upper()}</div></div></div></div></div><div class="section"><div class="section-title">⚖️ Module 3: Devil's Advocate Analysis</div><div class="analysis-card"><h3>🔎 Counter-Arguments</h3><ul>{counter_args_html}</ul></div><div class="analysis-card"><h3>❓ Critical Questions</h3><ul>{questions_html}</ul></div><div class="analysis-card"><h3>📊 Claim Complexity</h3><div class="stat-value">{devils_adv.get('complexity_score',0)}/8</div><div>Critical Thinking Level: {devils_adv.get('critical_thinking_level','unknown').upper()}</div></div></div><div class="section"><div class="section-title">📈 Temporal & Domain Analysis</div><div class="analysis-card"><h3>🌍 Domain Information</h3><div><strong>Domain:</strong> {temporal['domain'].title()}</div><div><strong>Description:</strong> {temporal['domain_description']}</div><div><strong>Freshness:</strong> {temporal['freshness_indicator']} ({temporal['freshness_score']:.0%})</div><div><strong>Status:</strong> {temporal['status'].upper()}</div></div></div>'''
    if sentiment:
        html_content+=f'''<div class="section"><div class="section-title">📊 Sentiment & Psychological Analysis</div><div class="analysis-card"><h3>Sentiment Breakdown</h3><div class="stats-grid"><div class="stat-box"><div class="stat-label">Positive</div><div class="stat-value">{sentiment.get('positive',0):.1%}</div></div><div class="stat-box"><div class="stat-label">Negative</div><div class="stat-value">{sentiment.get('negative',0):.1%}</div></div><div class="stat-box"><div class="stat-label">Urgency</div><div class="stat-value">{sentiment.get('urgency',0):.1%}</div></div><div class="stat-box"><div class="stat-label">Manipulation</div><div class="stat-value">{sentiment.get('manipulation_language',0):.1%}</div></div></div></div>'''
    if pressure:
        html_content+=f'''<div class="analysis-card"><h3>⚡ Psychological Pressure</h3><div><strong>Overall Pressure Level:</strong> {pressure.get('pressure_level','unknown').upper()}</div><div><strong>Total Pressure Score:</strong> {pressure.get('total_pressure_score',0):.0%}</div></div></div>'''
    if recommendations_html:
        html_content+=f'''<div class="section"><div class="section-title">💡 Recommendations & Warnings</div><div class="analysis-card"><ul>{recommendations_html}</ul></div></div>'''
    html_content+=f'''<div class="meta-info"><strong>Domain:</strong> {temporal['domain'].title()} | <strong>Generated:</strong> {timestamp} | <strong>Analysis ID:</strong> {analysis.get('knowledge_graph_node_id','N/A')}</div></div><div class="footer"><div style="font-size:36px;margin-bottom:10px;">🛡️</div><strong>ADVANCED INTEGRATED SENTINEL-RAG SYSTEM</strong><div>Critical Thinking • Manipulation Detection • Temporal Analysis</div></div></div></body></html>'''
    return html_content

def save_html_report(html,fn="advanced_report.html"):
    with open(fn,'w',encoding='utf-8')as f:
        f.write(html)
    print(f"✅ Report saved: {fn}")

print("Part 4 loaded: Integrated system and API ready")
"""ADVANCED INTEGRATED SENTINEL-RAG SYSTEM - PART 5 OF 5
Main Program Interface and Execution"""

def display_advanced_results(result):
    temporal=result['temporal_analysis']
    entities=result['temporal_entities']
    decay=result['decay_analysis']
    profile=result['domain_profile']
    manip=result['manipulation_analysis']
    fallacy=result['fallacy_analysis']
    trust=result['trust_score']
    
    print("\n"+"="*90)
    print("🎯 TRUST SCORE ANALYSIS")
    print("="*90)
    print(f"Score: {trust['score']}/100")
    print(f"Verdict: {trust['verdict']}")
    print(f"Risk Category: {trust['risk_category'].upper()}")
    print(f"Recommendation: {trust['recommendation']}")
    
    print("\n"+"="*90)
    print("🔍 MANIPULATION DETECTION")
    print("="*90)
    print(f"Type: {manip['manipulation_type'].upper()}")
    print(f"Confidence: {manip['confidence']:.1%}")
    print(f"Risk Level: {manip['risk_level'].upper()}")
    print(f"Neural Impact: {manip.get('neural_impact','N/A').upper()}")
    print(f"Pattern Strength: {manip.get('pattern_strength',0):.1%}")
    print(f"Explanation: {manip['explanation']}")
    if manip.get('indicators'):
        print(f"Indicators: {', '.join(manip['indicators'][:5])}")
    if manip.get('psychological_markers'):
        print(f"Psychological Markers: {', '.join(manip['psychological_markers'][:5])}")
    
    print("\n"+"="*90)
    print("🧠 FALLACY DETECTION")
    print("="*90)
    print(f"Type: {fallacy['fallacy_type'].upper()}")
    print(f"Severity: {fallacy['severity'].upper()}")
    print(f"Fallacy Count: {fallacy.get('fallacy_count',0)}")
    print(f"Logical Structure: {fallacy.get('logical_structure','N/A').upper()}")
    print(f"Explanation: {fallacy['explanation']}")
    
    print("\n"+"="*90)
    print("📅 TEMPORAL ANALYSIS")
    print("="*90)
    print(f"Domain: {temporal['domain'].upper()}")
    print(f"Description: {temporal['domain_description']}")
    print(f"Freshness: {temporal['freshness_indicator']} ({temporal['freshness_score']:.1%})")
    print(f"Status: {temporal['status'].upper()}")
    print(f"Time Sensitivity: {'YES' if temporal['time_sensitivity'] else 'NO'}")
    print(f"Outdated Risk: {temporal['outdated_risk'].upper()}")
    if temporal['key_topics']:
        print(f"Key Topics: {', '.join(temporal['key_topics'])}")
    
    print("\n"+"="*90)
    print("⚖️ DEVIL'S ADVOCATE ANALYSIS")
    print("="*90)
    devils_adv=result['devils_advocate_analysis']
    print(f"Claim Complexity: {devils_adv.get('complexity_score',0)}/8")
    print(f"Critical Thinking Level: {devils_adv.get('critical_thinking_level','unknown').upper()}")
    print("\nCounter-Arguments:")
    for i,arg in enumerate(devils_adv['counter_arguments'][:5],1):
        print(f"  {i}. {arg}")
    print("\nProbing Questions:")
    for i,q in enumerate(devils_adv['probing_questions'][:5],1):
        print(f"  {i}. {q}")
    
    if'sentiment_analysis'in result:
        print("\n"+"="*90)
        print("📊 SENTIMENT & PSYCHOLOGICAL ANALYSIS")
        print("="*90)
        sent=result['sentiment_analysis']
        print(f"Positive: {sent.get('positive',0):.1%}")
        print(f"Negative: {sent.get('negative',0):.1%}")
        print(f"Urgency: {sent.get('urgency',0):.1%}")
        print(f"Manipulation Language: {sent.get('manipulation_language',0):.1%}")
        print(f"Neutrality: {sent.get('neutrality',0):.1%}")
    
    if'psychological_pressure'in result:
        pressure=result['psychological_pressure']
        print(f"\nPsychological Pressure Level: {pressure.get('pressure_level','unknown').upper()}")
        print(f"Total Pressure Score: {pressure.get('total_pressure_score',0):.1%}")
    
    if result['recommendations']:
        print("\n"+"="*90)
        print("💡 RECOMMENDATIONS & WARNINGS")
        print("="*90)
        for i,rec in enumerate(result['recommendations'][:8],1):
            print(f"{i}. {rec}")
    
    print("\n"+"="*90)
    print("📋 METADATA")
    print("="*90)
    print(f"Analysis Timestamp: {result['metadata']['analysis_timestamp']}")
    print(f"Text Length: {result['metadata']['text_length']} characters")
    print(f"Knowledge Graph Node ID: {result['knowledge_graph_node_id']}")
    print(f"LLM Enhanced: {'YES' if result['metadata'].get('llm_enhanced') else 'NO'}")
    print(f"ML Enhanced: {'YES' if result['metadata'].get('ml_enhanced') else 'NO'}")
    print("="*90)

def main():
    print("\n"+"="*90)
    print("🛡️  ADVANCED INTEGRATED SENTINEL-RAG SYSTEM")
    print("="*90)
    print("Features: Advanced Manipulation Detection • Temporal Analysis • Linguistic Fingerprinting")
    print("Components: ML Enhancement • Knowledge Graph • API Server • Batch Processing")
    print("="*90+"\n")
    
    if not os.environ.get("ANTHROPIC_API_KEY"):
        print("\n❌ ERROR: ANTHROPIC_API_KEY not found!")
        print("\nSet your API key:")
        print("  Windows CMD: set ANTHROPIC_API_KEY=your-key-here")
        print("  Windows PowerShell: $env:ANTHROPIC_API_KEY='your-key-here'")
        print("  Mac/Linux: export ANTHROPIC_API_KEY='your-key-here'")
        return
    
    system=IntegratedAdvancedSystem()
    last_result=None
    
    while True:
        print("\n"+"="*90)
        print("MAIN MENU")
        print("="*90)
        print("1. Analyze Single Text (Advanced)")
        print("2. Compare Two Texts")
        print("3. Batch Analysis (CSV/JSON)")
        print("4. View System Analytics")
        print("5. View Knowledge Graph Statistics")
        print("6. View Analysis History")
        print("7. View Database Statistics")
        print("8. Configure Advanced Settings")
        print("9. Start API Server")
        print("10. Create User & API Key")
        print("11. Clear Cache")
        print("12. Generate HTML Report (Last Analysis)")
        print("13. Export Data")
        print("14. Exit")
        
        choice=input("\nEnter your choice (1-14): ").strip()
        
        if choice=="1":
            print("\n"+"─"*90)
            print("Enter your text to analyze (press Enter twice when done):")
            print("─"*90)
            lines=[]
            while True:
                line=input()
                if line==""and lines and lines[-1]=="":
                    break
                lines.append(line)
            text="\n".join(lines[:-1])if lines else""
            
            if not text.strip():
                print("\n❌ No text entered!")
                continue
            
            print("\n⏳ Performing advanced analysis...")
            result=system.comprehensive_advanced_analysis(text)
            db_manager.save_analysis(text,result)
            display_advanced_results(result)
            last_result=result
        
        elif choice=="2":
            print("\n"+"─"*90)
            print("Enter FIRST text (press Enter twice when done):")
            print("─"*90)
            lines1=[]
            while True:
                line=input()
                if line==""and lines1 and lines1[-1]=="":
                    break
                lines1.append(line)
            text1="\n".join(lines1[:-1])if lines1 else""
            
            print("\n"+"─"*90)
            print("Enter SECOND text (press Enter twice when done):")
            print("─"*90)
            lines2=[]
            while True:
                line=input()
                if line==""and lines2 and lines2[-1]=="":
                    break
                lines2.append(line)
            text2="\n".join(lines2[:-1])if lines2 else""
            
            if not text1.strip()or not text2.strip():
                print("\n❌ Both texts are required!")
                continue
            
            print("\n⏳ Analyzing and comparing...")
            result=system.comprehensive_advanced_analysis(text1,compare_text=text2)
            db_manager.save_analysis(text1,result)
            display_advanced_results(result)
            last_result=result
        
        elif choice=="3":
            inf=input("\nInput file (CSV/JSON): ").strip()
            if inf and os.path.exists(inf):
                print("\n⏳ Processing batch analysis...")
                texts=[]
                if inf.endswith('.csv'):
                    with open(inf,'r',encoding='utf-8')as f:
                        for row in csv.DictReader(f):
                            t=row.get('text','')
                            if t:
                                texts.append(t)
                elif inf.endswith('.json'):
                    with open(inf,'r',encoding='utf-8')as f:
                        d=json.load(f)
                        if isinstance(d,list):
                            for i in d:
                                t=i.get('text','')if isinstance(i,dict)else str(i)
                                if t:
                                    texts.append(t)
                
                results=system.batch_analyze(texts)
                for r in results:
                    db_manager.save_analysis(r['analyzed_text'],r)
                
                print(f"\n✅ Processed {len(results)} texts")
                
                outf=input("Save results to file? (filename or Enter to skip): ").strip()
                if outf:
                    with open(outf,'w',encoding='utf-8')as f:
                        json.dump(results,f,indent=2)
                    print(f"📄 Results saved to: {outf}")
            else:
                print("❌ File not found")
        
        elif choice=="4":
            analytics=system.get_analytics()
            print("\n"+"="*90)
            print("📊 SYSTEM ANALYTICS")
            print("="*90)
            for key,value in analytics.items():
                print(f"{key.replace('_',' ').title()}: {value}")
        
        elif choice=="5":
            stats=system.get_graph_statistics()
            graph_data=system.get_knowledge_graph()
            print("\n"+"="*90)
            print("🕸️ KNOWLEDGE GRAPH STATISTICS")
            print("="*90)
            print(f"Total Nodes: {graph_data['total_nodes']}")
            print(f"Total Edges: {graph_data['total_edges']}")
            print(f"Average Confidence: {stats['average_confidence']}")
            print("\nStatus Distribution:")
            for status,count in stats['status_distribution'].items():
                print(f"  {status.upper()}: {count}")
            print("\nDomain Distribution:")
            for domain,count in stats['domain_distribution'].items():
                print(f"  {domain.upper()}: {count}")
            print("\nManipulation Clusters:")
            for manip_type,node_ids in stats.get('manipulation_clusters',{}).items():
                print(f"  {manip_type.upper()}: {len(node_ids)} instances")
        
        elif choice=="6":
            history=system.get_history()
            print("\n"+"="*90)
            print("📜 ANALYSIS HISTORY")
            print("="*90)
            if not history:
                print("No analysis history available")
            else:
                for idx,item in enumerate(history[-20:],1):
                    print(f"\n{idx}. Timestamp: {item['timestamp']}")
                    print(f"   Domain: {item['domain']} | Trust: {item['trust_score']}/100")
                    print(f"   Freshness: {item['freshness']:.1%} | Node ID: {item['node_id']}")
                    print(f"   Manipulation: {item['manipulation']} | Fallacy: {item['fallacy']}")
        
        elif choice=="7":
            stats=db_manager.get_statistics()
            print("\n"+"="*90)
            print("💾 DATABASE STATISTICS")
            print("="*90)
            print(f"Total Analyses: {stats['total_analyses']}")
            print(f"Average Trust Score: {stats['average_trust_score']:.2f}")
            print(f"Average Freshness: {stats.get('average_freshness',0):.2f}")
            print("\nManipulation Distribution:")
            for k,v in stats['manipulation_distribution'].items():
                print(f"  {k}: {v}")
            print("\nFallacy Distribution:")
            for k,v in stats['fallacy_distribution'].items():
                print(f"  {k}: {v}")
            print("\nDomain Distribution:")
            for k,v in stats.get('domain_distribution',{}).items():
                print(f"  {k}: {v}")
        
        elif choice=="8":
            print("\n"+"="*90)
            print("⚙️ ADVANCED CONFIGURATION")
            print("="*90)
            print(f"1. Manipulation Weight: {config_manager.config['manipulation_weight_advanced']}")
            print(f"2. Fallacy Weight: {config_manager.config['fallacy_weight']}")
            print(f"3. Linguistic Weight: {config_manager.config['linguistic_weight']}")
            print(f"4. Temporal Weight: {config_manager.config['temporal_weight']}")
            print(f"5. High Risk Threshold: {config_manager.config['high_risk_threshold']}")
            print(f"6. Medium Risk Threshold: {config_manager.config['medium_risk_threshold']}")
            
            update_choice=input("\nUpdate settings? (y/n): ").lower()
            if update_choice=='y':
                try:
                    mw=float(input(f"Manipulation weight (current: {config_manager.config['manipulation_weight_advanced']}): ").strip()or config_manager.config['manipulation_weight_advanced'])
                    fw=float(input(f"Fallacy weight (current: {config_manager.config['fallacy_weight']}): ").strip()or config_manager.config['fallacy_weight'])
                    lw=float(input(f"Linguistic weight (current: {config_manager.config['linguistic_weight']}): ").strip()or config_manager.config['linguistic_weight'])
                    tw=float(input(f"Temporal weight (current: {config_manager.config['temporal_weight']}): ").strip()or config_manager.config['temporal_weight'])
                    config_manager.update_advanced_weights(lw,tw,mw)
                    config_manager.update_weights(mw,fw)
                    print("✅ Configuration updated")
                except:
                    print("❌ Invalid input")
        
        elif choice=="9":
            port=int(input("\nPort (default 8080): ").strip()or"8080")
            print("\n🚀 Starting API server...")
            threading.Thread(target=start_integrated_api_server,args=(system,port),daemon=True).start()
            input("\nPress Enter to stop server...")
        
        elif choice=="10":
            un=input("\nUsername: ").strip()
            pw=input("Password: ").strip()
            if un and pw:
                ak=db_manager.create_user(un,pw)
                print(f"\n✅ User created successfully!")
                print(f"🔑 API Key: {ak}")
                print("⚠️  Save this key securely!")
        
        elif choice=="11":
            result_msg=system.clear_cache()
            print(f"\n✅ {result_msg}")
        
        elif choice=="12":
            if last_result:
                filename=input("\nFilename (default 'advanced_report.html'): ").strip()
                if not filename:
                    filename="advanced_report.html"
                html=generate_advanced_html_report(last_result)
                save_html_report(html,filename)
            else:
                print("\n❌ No analysis available. Run an analysis first.")
        
        elif choice=="13":
            filename=input("\nExport filename (JSON): ").strip()
            if filename:
                export_data={"analytics":system.get_analytics(),"knowledge_graph":system.get_knowledge_graph(),"graph_statistics":system.get_graph_statistics(),"history":system.get_history(),"database_statistics":db_manager.get_statistics()}
                with open(filename,'w',encoding='utf-8')as f:
                    json.dump(export_data,f,indent=2)
                print(f"✅ Data exported to: {filename}")
        
        elif choice=="14":
            print("\n👋 Thank you for using the Advanced Integrated Sentinel-RAG System!")
            print("🛡️ Stay critical. Stay informed. Stay protected.")
            break
        
        else:
            print("\n❌ Invalid choice! Please enter 1-14")

if __name__=="__main__":
    main()

print("\nPart 5 loaded: Main program interface ready")
print("="*90)
print("🎉 ALL COMPONENTS LOADED SUCCESSFULLY")
print("="*90)
print("\nTo run the integrated system:")
print("1. Ensure ANTHROPIC_API_KEY is set")
print("2. Execute: python integrated_sentinel_rag.py")
print("3. Follow the interactive menu")
print("\nSystem Features:")
print("✓ Advanced manipulation detection (12 patterns)")
print("✓ Enhanced fallacy detection (12 types)")
print("✓ Temporal analysis with domain-specific decay")
print("✓ Linguistic fingerprinting")
print("✓ ML-enhanced detection")
print("✓ Knowledge graph tracking")
print("✓ RESTful API server")
print("✓ Batch processing")
print("✓ Database persistence")
print("✓ HTML report generation")
print("="*90)
