import json
import spacy
from spacy.training import Example
from nltk.tokenize import sent_tokenize
nlp = spacy.load("ru_core_news_sm")


def find_substring_indexes(text, entities: dict):
    res = []
    for entity, value in entities.items():
        for v in value:
            for index in range(len(text)):
                if text.startswith(str(v), index):
                    res.append((index, index+len(v), entity))
    return {"entities": res}


def clear_text(text):
    text, entities = text
    sents = sent_tokenize(text)
    res = []
    for i in sents:
        entity = find_substring_indexes(i, entities)
        if entity['entities'] != []:
            res.append((i, entity))
    return res
    

f = open("./data/data.json", 'r')
texts = json.load(f)
f.close()
train_data = []
for i in texts:
    train_data += clear_text(i)


def train_ner_model(train_data, iterations=120):
    nlp_ner = spacy.blank("ru")
    ner = nlp_ner.add_pipe("ner")
    
    for _, annotations in train_data:
        for ent in annotations.get("entities"):
            ner.add_label(ent[2])

    optimizer = nlp_ner.begin_training()
    for _ in range(iterations):
        losses = {}
        examples = [
            Example.from_dict(nlp.make_doc(text), annotations) 
            for text, annotations in train_data
        ]
        nlp_ner.update(examples, drop=0.5, losses=losses)
        print(losses)
    return nlp_ner

def extract_entities(text, ner_model):
    doc = ner_model(text)
    entities = [(ent.text, ent.label_) for ent in doc.ents]
    return entities

input_text = "Добрый день! Я вижу, у вас назначен диагноз мерцательная аритмия. Расскажите, пожалуйста, какие у вас возникают жалобы? Здравствуйте! Да, у меня часто возникают сердцебиения и ощущение перебоев в сердце.Хорошо, я занесу эту информацию в протокол осмотра. А теперь давайте приступим к осмотру. Каково ваше общее состояние?В целом я чувствую себя нормально, но иногда устаю быстрее обычного.Хорошо, занесу это в протокол. А какая у вас температура тела?Последний раз измерялась 36.8 градусов Цельсия.Отлично. Теперь нам понадобятся данные о вашем ИМТ, росте, весе и окружности талии.Мой ИМТ составляет 25 кг/кв.м, рост 175 см, вес 70 кг, а окружность талии 85 см. АД сидя составляет 130/80 мм рт.ст., а лежа - 120/75 мм рт.ст. Спасибо за информацию. Давайте продолжим. Как вы оцениваете свое сознание?Сознание ясное, никаких проблем не замечаю.Занесу это в протокол. Теперь прошу вас оценить состояние кожных покровов и видимых слизистых.Кожа цвета нормального, без высыпаний или покраснений. Слизистые тоже выглядят нормально"
trained_ner_model = train_ner_model(train_data)
extracted_entities = extract_entities(input_text, trained_ner_model)
print(extracted_entities)

trained_ner_model.to_disk("./NER")

nlp = spacy.load("./NER")
extracted_entities = extract_entities(input_text, nlp)
print(extracted_entities)