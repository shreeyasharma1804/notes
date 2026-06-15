### Simple RNN

<img width="733" height="544" alt="image" src="https://github.com/user-attachments/assets/b3a261b5-2c2a-4d9b-ae21-2003fadb43a0" />

A single RNN unit computes:

$$$
y_t = f(w_1 x_t + w_2 y_{t-1} + b_1)
$$$

Here, f is the activation function

Output layer equation:

$$$
\hat{o}_t = w_3 y_t + b_2
$$$
