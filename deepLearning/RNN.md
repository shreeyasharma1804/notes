### Simple RNN

<img width="733" height="544" alt="image" src="https://github.com/user-attachments/assets/b3a261b5-2c2a-4d9b-ae21-2003fadb43a0" />

- A single RNN unit computes:

$$
y_t = f(w_1 x_t + w_2 y_{t-1} + b_1)
$$

Here, f is the activation function

- Output layer equation:

$$
\hat{o}_t = w_3 y_t + b_2
$$

- These networks are used for predictions with variable input size
- These networks also suffer with gradient explode, vanish, since during the last inputs, the {w_2} weight has exponential presence.
- The output of this RNN is its feedback value

### LSTM

<img width="1015" height="576" alt="image" src="https://github.com/user-attachments/assets/2fe6f342-f562-4587-bc85-aae35b39a381" />

- These cells do not go through the vanishing/exploding gradient problem
- The outputs are the long and short term memory

