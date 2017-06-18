# -*- coding: utf-8 -*-

from model import *
from preprocess import *
from config import Config
from utils import wer, now

def evaluate(input_variable, len_inputs):
    batch_size, input_length = input_variable.size()

    # Run through encoder
    encoder_hidden = encoder.init_hidden(batch_size)
    encoder_outputs, encoder_hidden = encoder(input_variable, len_inputs, encoder_hidden)

    # Create starting vectors for decoder
    decoder_input = Variable(torch.LongTensor([[SOS_token] for _ in range(batch_size)]))  # SOS
    decoder_context = Variable(torch.zeros(batch_size, decoder.hidden_size))
    decoder_hidden = encoder_hidden
    if Config.use_cuda:
        decoder_input = decoder_input.cuda()
        decoder_context = decoder_context.cuda()

    decoded_output = torch.zeros(batch_size, Config.max_seq_length, out=torch.LongTensor(batch_size, Config.max_seq_length))
    decoder_attentions = torch.zeros(batch_size, input_length, input_length)

    # Run through decoder
    for di in range(Config.max_seq_length):
        decoder_output, decoder_context, decoder_hidden, decoder_attention = decoder(decoder_input, decoder_context,
                                                                                     decoder_hidden, encoder_outputs)
        # decoder_attentions[:, di, :decoder_attention.size(2)] += decoder_attention.squeeze(0).squeeze(0).cpu().data

        # Choose top word from output
        _, top_index = decoder_output.data.topk(1)

        decoded_output[:, di] = top_index

        # Next input is chosen word
        decoder_input = Variable(top_index)
        if Config.use_cuda: decoder_input = decoder_input.cuda()

    return decoded_output  #, decoder_attentions[:, di + 1, :len(encoder_outputs)]


_, eval_corpus, word_dict = build_corpus()
encoder, decoder = get_model(word_dict.n_words)

inputs, targets, len_inputs, _ = eval_corpus.next_batch(100)
input_variable = Variable(torch.LongTensor(inputs), requires_grad=False)
if Config.use_cuda:
    input_variable = input_variable.cuda()

output_tensor = evaluate(input_variable, len_inputs)
output_words = output_tensor.cpu().numpy().tolist()

print('WER:\t{}'.format(np.mean(map(lambda (a, b): wer(a, b), zip(output_words, targets)))))

print('SRC:\t{}'.format(word_dict.indexes_to_sentence(inputs[0])))
print('PRE:\t{}'.format(word_dict.indexes_to_sentence(output_words[0])))
print('TRU:\t{}'.format(word_dict.indexes_to_sentence(targets[0])))