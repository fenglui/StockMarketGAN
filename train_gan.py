import os
import pandas as pd
from gan import GAN
import random
import tensorflow as tf


class TrainGan:

    def __init__(self, num_historical_days, batch_size=128):
        self.batch_size = batch_size
        self.data = []
        files = [os.path.join('./stock_data', f) for f in os.listdir('./stock_data')]
        for file in files:
            print(file)
            #Read in file -- note that parse_dates will be need later
            df = pd.read_csv(file, index_col='Date', parse_dates=True)
            df = df[['Open','High','Low','Close','Volume']]
            #Normilize using a of size num_historical_days
            df = ((df -
            df.rolling(num_historical_days).mean().shift(-num_historical_days))
            /(df.rolling(num_historical_days).max().shift(-num_historical_days)
            -df.rolling(num_historical_days).min().shift(-num_historical_days)))
            #Drop the last 10 day that we don't have data for
            df = df.dropna()
            #Create new index with missing days
            idx = pd.date_range(df.index[-1], df.index[0])
            #Reindex and fill the missing day with the value from the day before
            df = df.reindex(idx, method='ffill').sort_index(ascending=False)
            #Hold out the last year of trading for testing
            df = df[252:]
            #This may not create good samples if num_historical_days is a
            #mutliple of 7
            for i in range(num_historical_days, len(df), num_historical_days):
                self.data.append(df.values[i-num_historical_days:i])

        self.gan = GAN(num_features=5, num_historical_days=num_historical_days,
                        generator_input_size=100)

    def random_batch(self, batch_size=128):
        batch = []
        while True:
            batch.append(random.choice(self.data))
            if (len(batch) == batch_size):
                yield batch
                batch = []

    def train(self, print_steps=1000):
        sess = tf.Session()
        G_loss = 0
        D_loss = 0
        sess.run(tf.global_variables_initializer())
        for i, X in enumerate(self.random_batch(self.batch_size)):
            if i % 1 == 0:
                _, D_loss_curr = sess.run([self.gan.D_solver, self.gan.D_loss], feed_dict=
                        {self.gan.X:X, self.gan.Z:self.gan.sample_Z(self.batch_size, 100)})
                D_loss += D_loss_curr
            if i % 1 == 0:
                _, G_loss_curr = sess.run([self.gan.G_solver, self.gan.G_loss],
                        feed_dict={self.gan.Z:self.gan.sample_Z(self.batch_size, 100)})
                G_loss += G_loss_curr
            if i % print_steps == 0:
                print('Step={} D_loss={}, G_loss={}'.format(i, D_loss/print_steps, G_loss/print_steps))
                G_loss = 0
                D_loss = 0



gan = TrainGan(20, 128)
gan.train()
