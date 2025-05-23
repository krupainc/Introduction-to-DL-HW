# -*- coding: utf-8 -*-
"""hw_2_krupitsa__1.ipynb

Automatically generated by Colab.

Original file is located at
    https://colab.research.google.com/drive/1_qPo_CylMFbZcRo9T6jcYp21weeknZ2D

# Домашнее задание 2. Классификация изображений.

В этом задании потребуется обучить классификатор изображений. Будем работать с датасетом, название которого раскрывать не будем. Можете посмотреть самостоятельно на картинки, которые в есть датасете. В нём 200 классов и около 5 тысяч картинок на каждый класс. Классы пронумерованы, как нетрудно догадаться, от 0 до 199. Скачать датасет можно вот [тут](https://yadi.sk/d/BNR41Vu3y0c7qA).

Структура датасета простая -- есть директории train/ и val/, в которых лежат обучающие и валидационные данные. В train/ и val/ лежат директориии, соответствующие классам изображений, в которых лежат, собственно, сами изображения.

__Задание__. Необходимо выполнить два задания

1) Добейтесь accuracy **на валидации не менее 0.44**. В этом задании **запрещено** пользоваться предобученными моделями и ресайзом картинок. 5 баллов

2) Добейтесь accuracy **на валидации не менее 0.84**. В этом задании делать ресайз и использовать претрейн можно. 5 баллов

Напишите краткий отчёт о проделанных экспериментах. Что сработало и что не сработало? Почему вы решили, сделать так, а не иначе? Обязательно указывайте ссылки на чужой код, если вы его используете. Обязательно ссылайтесь на статьи / блогпосты / вопросы на stackoverflow / видосы от ютуберов-машинлернеров / курсы / подсказки от Дяди Васи и прочие дополнительные материалы, если вы их используете.

Ваш код обязательно должен проходить все `assert`'ы ниже.

__Использовать внешние данные для обучения строго запрещено в обоих заданиях. Также запрещено обучаться на валидационной выборке__.


__Критерии оценки__: Оценка вычисляется по простой формуле: `min(10, 10 * Ваша accuracy / 0.44)` для первого задания и `min(10, 10 * (Ваша accuracy - 0.5) / 0.34)` для второго. Оценка округляется до десятых по арифметическим правилам.


__Советы и указания__:
 - Наверняка вам потребуется много гуглить о классификации и о том, как заставить её работать. Это нормально, все гуглят. Но не забывайте, что нужно быть готовым за скатанный код отвечать :)
 - Используйте аугментации. Для этого пользуйтесь модулем `torchvision.transforms` или библиотекой [albumentations](https://github.com/albumentations-team/albumentations)
 - Можно обучать с нуля или файнтюнить (в зависимости от задания) модели из `torchvision`.
 - Рекомендуем написать вам сначала класс-датасет (или воспользоваться классом `ImageFolder`), который возвращает картинки и соответствующие им классы, а затем функции для трейна по шаблонам ниже. Однако делать это мы не заставляем. Если вам так неудобно, то можете писать код в удобном стиле. Однако учтите, что чрезмерное изменение нижеперечисленных шаблонов увеличит количество вопросов к вашему коду и повысит вероятность вызова на защиту :)
 - Валидируйте. Трекайте ошибки как можно раньше, чтобы не тратить время впустую.
 - Чтобы быстро отладить код, пробуйте обучаться на маленькой части датасета (скажем, 5-10 картинок просто чтобы убедиться что код запускается). Когда вы поняли, что смогли всё отдебажить, переходите обучению по всему датасету
 - На каждый запуск делайте ровно одно изменение в модели/аугментации/оптимайзере, чтобы понять, что и как влияет на результат.
 - Фиксируйте random seed.
 - Начинайте с простых моделей и постепенно переходите к сложным. Обучение лёгких моделей экономит много времени.
 - Ставьте расписание на learning rate. Уменьшайте его, когда лосс на валидации перестаёт убывать.
 - Советуем использовать GPU. Если у вас его нет, используйте google colab. Если вам неудобно его использовать на постоянной основе, напишите и отладьте весь код локально на CPU, а затем запустите уже написанный ноутбук в колабе. Авторское решение задания достигает требуемой точности в колабе за 15 минут обучения.

Good luck & have fun! :)
"""

!pip install wandb -q
!pip3 install pytorch_lightning torchmetrics -q

# Возможно ниже будет не очень работать WandbLogger с первого разу, перезапустите kernel тетрадки
import wandb

wandb.login()

import math
import os
import random
import sys

import matplotlib.pyplot as plt
import numpy as np
import pytorch_lightning as pl
import torch
import torchvision
import torchvision.transforms as transforms
from PIL import Image
from pytorch_lightning.loggers import WandbLogger
from torch import nn
from torch.nn import functional as F
from torch.utils.data import DataLoader
from torchmetrics.functional import accuracy
from torchvision.datasets import ImageFolder
from tqdm import tqdm

# You may add any imports you need

def seed_everything(seed):
    # Фискирует максимум сидов.
    # Это понадобится, чтобы сравнение оптимизаторов было корректным
    random.seed(seed)
    os.environ["PYTHONHASHSEED"] = str(seed)
    np.random.seed(seed)
    torch.manual_seed(seed)
    torch.cuda.manual_seed(seed)
    torch.backends.cudnn.deterministic = True


seed_everything(123456)

!wget https://www.dropbox.com/s/33l8lp62rmvtx40/dataset.zip?dl=1 -O dataset.zip && unzip -q dataset.zip

"""## Задание 0

### Что поможет сделать на 10 из 10 (одно задание - 5 баллов)

1. Использовать все возможные методы оптимизации и эксперемнтировать с ними.
2. Подбор learning rate. Пример из прошлого семинара как это делать: [Как найти lr](https://pytorch-lightning.readthedocs.io/en/1.4.5/advanced/lr_finder.html)

```
  trainer = pl.Trainer(accelerator="gpu", max_epochs=2, auto_lr_find=True)

  trainer.tune(module, train_dataloader, eval_dataloader)

  trainer.fit(module, train_dataloader, eval_dataloader))
```



3. Аугментация данных. [Документация (полезная)](https://pytorch.org/vision/main/transforms.html), а также [библиотека albumentation](https://towardsdatascience.com/getting-started-with-albumentation-winning-deep-learning-image-augmentation-technique-in-pytorch-47aaba0ee3f8)
4. Подбор архитектуры модели.
5. Можно написать модель руками свою в YourNet, а можно импортировать не предобученную сетку известной архитектуры из модуля torchvision.models. Один из способов как можно сделать:

  * `torchvision.models.resnet18(pretrained=False, num_classes=200).to(device)`
  * Документация по возможным моделям и как их можно брать: [Документация (полезная)](https://pytorch.org/vision/stable/models.html)
6. Правильно нормализовывать данные при создании, пример [тык, но тут и в целом гайд от и до](https://www.pluralsight.com/guides/image-classification-with-pytorch)
7. Model Checkpointing. Сохраняйте свой прогресс (модели), чтобы когда что-то пойдет не так вы сможете начать с этого места или просто воспроизвести свои результаты модели, которые обучали.
 * Пример как можно с wandb тут: [Сохраняем лучшие модели в wandb](https://docs.wandb.ai/guides/integrations/lightning)
 * По простому можно так: [Сохраняем модели в pytorch дока](https://pytorch.org/tutorials/beginner/saving_loading_models.html)

### Подготовка данных
"""

import PIL
train_transform =  transforms.Compose(
    [   transforms.ColorJitter(hue=.05, saturation=.05),
        transforms.RandomHorizontalFlip(),
        transforms.RandomRotation(20, resample=PIL.Image.BILINEAR),
        transforms.ToTensor(),

    ]
)
val_transform =  transforms.Compose(
    [
        transforms.ToTensor(),

    ]
)

train_dataset = ImageFolder('/content/dataset/dataset/train', transform=train_transform)
val_dataset = ImageFolder('/content/dataset/dataset/val', transform=val_transform)
# REPLACE ./dataset/dataset WITH THE FOLDER WHERE YOU DOWNLOADED AND UNZIPPED THE DATASET

means = []
vars = []
for image, label in tqdm(val_dataset):
    means.append(image.mean(dim = (1, 2)))
    vars.append(image.std(dim = (1, 2)))
torch.stack(means).mean(dim=0), torch.stack(vars).mean(dim=0)

means = []
vars = []
for image, label in tqdm(train_dataset):
    means.append(image.mean(dim = (1, 2)))
    vars.append(image.std(dim = (1, 2)))
torch.stack(means).mean(dim=0), torch.stack(vars).mean(dim=0)

# YOU CAN DEFINE AUGMENTATIONS HERE
# YOUR CODE HERE
import PIL
train_transform =  transforms.Compose(
    [   transforms.ColorJitter(hue=.05, saturation=.05),
        transforms.RandomHorizontalFlip(),
        transforms.RandomRotation(20, resample=PIL.Image.BILINEAR),
        transforms.ToTensor(),
        transforms.Normalize((0.4444, 0.4129, 0.3666), (0.2444, 0.2367, 0.2302))
    ]
)
val_transform =  transforms.Compose(
    [
        transforms.ToTensor(),
        transforms.Normalize((0.4824, 0.4495, 0.3981), (0.2301, 0.2264, 0.2261))
    ]
)

train_dataset = ImageFolder('/content/dataset/dataset/train', transform=train_transform)
val_dataset = ImageFolder('/content/dataset/dataset/val', transform=val_transform)
# REPLACE ./dataset/dataset WITH THE FOLDER WHERE YOU DOWNLOADED AND UNZIPPED THE DATASET

train_dataloader =  torch.utils.data.DataLoader(
    train_dataset,
    batch_size=256,
    shuffle=True,
)
val_dataloader =  torch.utils.data.DataLoader(
    val_dataset,
    batch_size=256,
    shuffle=False,
)

# Just very simple sanity checks
assert isinstance(train_dataset[0], tuple)
assert len(train_dataset[0]) == 2
assert isinstance(train_dataset[1][1], int)
print("tests passed")

"""### Посмотрим на картиночки"""

for batch in val_dataloader:
    images, class_nums = batch
    plt.imshow(images[5].permute(1, 2, 0))
    plt.show()
    plt.imshow(images[19].permute(1, 2, 0))
    plt.show()
    break

"""## Задание 1.

5 баллов
Добейтесь accuracy на валидации не менее 0.44. В этом задании запрещено пользоваться предобученными моделями и ресайзом картинок.


Для того чтобы выбить скор (считается ниже) на 2.5/5 балла (то есть половину за задание) достаточно соблюдать пару простых жизненных правил:
1. Аугментация (без нее сложно очень будет)
2. Оптимайзеры можно (и нужно) использовать друг с другом. Однако когда что-то проверяете, то не меняйте несколько параметров сразу - собьете логику экспериментов
3. Не используйте полносвязные модели или самые первые сверточные, используйте более современные архитектуры (что на лекциях встречались)
4. Посмотреть все ноутбуки прошедших семинаров и слепить из них что-то общее. Семинарских тетрадок хватит сверх

Я честно хотела прописать все эксперименты но у меня подло закончился гпу на самом интересном моменте после того как я пыталась обучить модель для второго задания на нескольких эпохах (абсолютно бесполезное занятие), поэтому приходится довольствоваться, тем что есть(((((
  

  Но я все таки распишу, что происходило и как я дошла к тому, что имею - просто экспериментов ниже не будет, потому что я останавливала почти все сразу же, как понимала, что на первой эпохе качество меньше чем 0,1.


  Сначала я очень долго боролась с тем, что модель выдавала acc постоянно 0,005 вне зависимости от эпох и аугментаций, но тогда я решила убрать автоматический подбор lr - и это помогло! На вручную поставленном lr = 0.001 модель действительно начала учиться и в общем то следующий эксперимент - это как раз мои первые нормальные результаты.


  Стоит еще упомянуть, что я в свои первые разы долго использовала очень уж маленький батч 32, но потом тоже сообразила, что стоит брать больше, все таки выборка у нас огромная.


  Используя resnet у меня не было особо даже вариантов, что именно можно менять, чтобы качество подросло, но начитавшись советов в чате я решила, что может быть и аугментации вовсе не такие полезные, как казалось. Я оставила только горизонатальный флип по совету Макса Абрахама))))) и кажется это помогло.


  Стоит также сказать, что я не до конца разобралась, как именно работает мой код - мне честно очень тяжело было сообразить что-то красивое в колабе, поэтому для запуска нового эксперимента мне почему-то приходится запускать код с самого начала после того как я изменяю функцию для трансформа - в районе sanity check и вывода примеров картинок. Но в остальном все работает))))) В остальном кажется весь код - это буквально копии семинаров, самое главное было просто вставить правильные модели. Еще раз сори, что как-то некрасиво и неаккуратно сделано, я слишком торопилась(((

### Модель (или просто импортируйте не предобученную)
"""

import pytorch_lightning as pl
from torchmetrics.functional import accuracy
from torchvision.models import resnet18

model = resnet18(pretrained=True)
model

"""### Тренировочный класс lightning"""

class YourModule(pl.LightningModule):
    def __init__(self,  model, learning_rate = 0.001):
        super().__init__()
        self.model = model

        self.learning_rate = learning_rate

        self.optimizer = torch.optim.Adam(self.model.parameters(), lr = self.learning_rate)

        self.loss = nn.CrossEntropyLoss()

    def forward(self, x):

        preds = self.model(x)
        return preds

    def configure_optimizers(self):
        return self.optimizer

    def training_step(self, train_batch, batch_idx):
        images, target = train_batch
        preds = self.forward(images)
        loss = self.loss(preds, target)
        self.log("train_loss", loss, prog_bar=True)
        return loss

    def validation_step(self, val_batch, batch_idx):
        images, target = val_batch
        preds = self.forward(images)
        loss = self.loss(preds, target)
        acc = accuracy(torch.argmax(preds, dim=-1).long(), target.long())
        self.log("val_loss", loss, prog_bar=True)
        self.log("accuracy", acc, prog_bar=True)
        return acc

wandb_logger = WandbLogger(log_model='all') # какие возможности дает с pytorch_lightning https://docs.wandb.ai/guides/integrations/lightning
device = "cuda:0" if torch.cuda.is_available() else "cpu"

#model = YourNet().to() # YOUR CODE HERE
model = torchvision.models.resnet18(pretrained=False, num_classes=200).to(device)
module = YourModule(model)



"""Эксперимент 1. 10 эпох, вручную задала lr = 0.001, есть разная аугментация."""

trainer = pl.Trainer(logger=wandb_logger, accelerator = 'gpu', max_epochs = 10)  # YOUR CODE HERE
trainer.fit(module, train_dataloader, val_dataloader)  # YOUR CODE HERE

torch.save(module, '/content/modelka')

modelka = torch.load('/content/modelka')

"""### Валидация результатов задания"""

from sklearn.metrics import accuracy_score
import torch


def evaluate_task(model, test_dataloader, device="cuda:0" if torch.cuda.is_available() else "cpu"):
    model = model.to(device)
    predicted_classes = torch.Tensor([]).to(device)
    true_classes = torch.Tensor([]).to(device)

    model.eval()
    with torch.no_grad():
        for images, labels in tqdm(test_dataloader):
            images, labels = images.to(device), labels.to(device)

            pred = model(images)
            pred_classes = torch.argmax(pred, dim=-1)

            predicted_classes = torch.cat((predicted_classes, pred_classes), 0)
            true_classes = torch.cat((true_classes, labels), 0)

    return accuracy_score(predicted_classes.cpu().detach().numpy(), true_classes.cpu().detach().numpy())



accuracy = evaluate_task(modelka, val_dataloader)
print(f"Оценка за это задание составит {np.clip(10 * accuracy / 0.44, 0, 10):.2f} баллов")

"""Эксперимент 2. Попробую сделать 8 эпох и убрать аугментации кроме горизонтального поворота. lr = 0.001"""

# YOU CAN DEFINE AUGMENTATIONS HERE
# YOUR CODE HERE
import PIL
train_transform =  transforms.Compose(
    [
        transforms.RandomHorizontalFlip(),
        transforms.ToTensor(),
        transforms.Normalize((0.4444, 0.4129, 0.3666), (0.2444, 0.2367, 0.2302))
    ]
)
val_transform =  transforms.Compose(
    [
        transforms.ToTensor(),
        transforms.Normalize((0.4824, 0.4495, 0.3981), (0.2301, 0.2264, 0.2261))
    ]
)

train_dataset = ImageFolder('/content/dataset/dataset/train', transform=train_transform)
val_dataset = ImageFolder('/content/dataset/dataset/val', transform=val_transform)
# REPLACE ./dataset/dataset WITH THE FOLDER WHERE YOU DOWNLOADED AND UNZIPPED THE DATASET

train_dataloader =  torch.utils.data.DataLoader(
    train_dataset,
    batch_size=256,
    shuffle=True,
)
val_dataloader =  torch.utils.data.DataLoader(
    val_dataset,
    batch_size=256,
    shuffle=False,
)

model = torchvision.models.resnet18(pretrained=False, num_classes=200).to(device)
module = YourModule(model)
trainer = pl.Trainer(logger=wandb_logger, accelerator = 'gpu', max_epochs = 8)  # YOUR CODE HERE
trainer.fit(module, train_dataloader, val_dataloader)  # YOUR CODE HERE

torch.save(module, '/content/modelka_1')
modelka_1 = torch.load('/content/modelka_1')
accuracy = evaluate_task(modelka_1, val_dataloader)
print(f"Оценка за это задание составит {np.clip(10 * accuracy / 0.44, 0, 10):.2f} баллов")



"""## Задание 2

5 баллов
Добейтесь accuracy на валидации не менее 0.84. В этом задании делать ресайз и использовать претрейн можно.

Для того чтобы выбить скор (считается ниже) на 2.5/5 балла (то есть половину за задание) достаточно соблюдать пару простых жизненных правил:
1. Аугментация (без нее сложно очень будет)
2. Оптимайзеры можно (и нужно) использовать друг с другом. Однако когда что-то проверяете, то не меняйте несколько параметров сразу - собьете логику экспериментов
3. Не используйте полносвязные модели или самые первые сверточные, используйте более современные архитектуры (что на лекциях встречались или можете пойти дальше).
4. Попробуйте сначала посмотреть качество исходной модели без дообучения, сохраните как baseline. Отсюда поймете какие слои нужно дообучать.
5. Посмотреть все ноутбуки прошедших семинаров и слепить из них что-то общее. Семинарских тетрадок хватит сверх

Ну в этом задании такое высокое качество - просто удача. Я просто опять же по советам из чатика решила погуглить, какие модели хорошо работают на ImageNet и реализованы в торче, где-то услышала про ViT и решила реализовать его и с первого же раза он выбил такое классное качество.

### Модель (или просто импортируйте предобученную)
"""

import PIL
train_transform =  transforms.Compose(
    [   transforms.Resize((224, 224)),
        transforms.ColorJitter(hue=.05, saturation=.05),
        transforms.RandomHorizontalFlip(),
        transforms.RandomRotation(20, resample=PIL.Image.BILINEAR),
        transforms.ToTensor(),
        transforms.Normalize((0.4444, 0.4129, 0.3666), (0.2444, 0.2367, 0.2302))
    ]
)
val_transform =  transforms.Compose(
    [   transforms.Resize((224, 224)),
        transforms.ToTensor(),
        transforms.Normalize((0.4824, 0.4495, 0.3981), (0.2301, 0.2264, 0.2261))
    ]
)

train_dataset = ImageFolder('/content/dataset/dataset/train', transform=train_transform)
val_dataset = ImageFolder('/content/dataset/dataset/val', transform=val_transform)
# REPLACE ./dataset/dataset WITH THE FOLDER WHERE YOU DOWNLOADED AND UNZIPPED THE DATASET

train_dataloader =  torch.utils.data.DataLoader(
    train_dataset,
    batch_size=256,
    shuffle=True,
)
val_dataloader =  torch.utils.data.DataLoader(
    val_dataset,
    batch_size=256,
    shuffle=False,
)

from torchvision.models import vit_b_16
model = vit_b_16(pretrained = True)
model

"""### Тренировочный класс lightning"""

class YourModule(pl.LightningModule):
    def __init__(self, model, learning_rate = 0.001):
        super().__init__()
        self.model = model
        self.model.heads = nn.Identity()
        self.classifier = nn.Linear(768, 200)
        self.optimizer = torch.optim.Adam(self.classifier.parameters())
        self.loss = nn.CrossEntropyLoss()

    def forward(self, x):
        with torch.no_grad():
            features = self.model(x)
        preds = self.classifier(features)

        return preds
    def configure_optimizers(self):
        return self.optimizer

    def training_step(self, train_batch, batch_idx):
        images, target = train_batch
        preds = self.forward(images)
        loss = self.loss(preds, target)
        self.log("train_loss", loss, prog_bar=True)
        return loss

    def validation_step(self, val_batch, batch_idx):
        images, target = val_batch
        preds = self.forward(images)
        loss = self.loss(preds, target)
        acc = accuracy(torch.argmax(preds, dim=-1).long(), target.long())
        self.log("val_loss", loss, prog_bar=True)
        self.log("accuracy", acc, prog_bar=True)
        return acc

wandb_logger = WandbLogger(log_model='all') # какие возможности дает с pytorch_lightning https://docs.wandb.ai/guides/integrations/lightning
device =  "cuda:0" if torch.cuda.is_available() else "cpu"

model = torchvision.models.vit_b_16(pretrained=True).to(device)
module = YourModule(model)

trainer = pl.Trainer(logger=wandb_logger, accelerator = 'gpu', max_epochs = 1)  # YOUR CODE HERE
trainer.fit(module, train_dataloader, val_dataloader)  # YOUR CODE HERE

"""### Валидация результатов задания"""

torch.save(module, '/content/task_2')
modelka_2 = torch.load('/content/task_2')
accuracy = evaluate_task(modelka_2, val_dataloader)

print(f"Оценка за это задание составит {np.clip(10 * (accuracy - 0.5) / 0.34, 0, 10):.2f} баллов")

"""# Отчёт об экспериментах

текст писать тут (или ссылочку на wandb/любой трекер экспреиментов) для каждого задания, то есть не обязательно именно тут рисовать графики, если вы используете готовые трекеры/мониторинги ваших моделей.
"""

https://wandb.ai/krupa/lightning_logs/reports/Untitled-Report--VmlldzoyODkyNjc3?accessToken=1xn2wbhylft7b8ygue8ib80m5f38vsqqljfyw22xxfk6z0ekaub46vsxj7vq1x8j
