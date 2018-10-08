def read_dataset(fname):
    sentences = []
    tags = []
    alltag = []
    allcontent = []
    with open(fname) as f:
        content = f.readlines()
    # you may also want to remove whitespace characters like `\n` at the end of each line
    content = [x.strip() for x in content]
    idx_line = 0
    while idx_line < len(content):
        sent = []
        tag = []
        temp_content = []
        while not content[idx_line].startswith('</kalimat'):
            if  not content[idx_line].startswith('<kalimat'):
                content_part = content[idx_line].split('\t')
                sent.append(content_part[0].lower())
                tag.append(content_part[1])
                alltag.append(content_part[1])
                temp = content_part[0].lower(), content_part[1]
                temp_content.append(temp)
            idx_line = idx_line + 1
        sentences.append(sent)
        tags.append(tag)
        allcontent.append(temp_content)
        idx_line = idx_line + 2
    return sentences, tags, alltag, allcontent

sentences,tags,alltag,allcontent = read_dataset('Indonesian_Manually_Tagged_Corpus_ID_Viterbi_Training.tsv')

def read_dataset2(fname):
    sentences = []
    tags = []
    alltest = []
    with open(fname) as f:
        content = f.readlines()
    # you may also want to remove whitespace characters like `\n` at the end of each line
    content = [x.strip() for x in content]
    idx_line = 0
    while idx_line < len(content):
        sent = []
        tag = []
        temp_test = []
        while not content[idx_line].startswith('</kalimat'):
            if not content[idx_line].startswith('<kalimat'):
                content_part = content[idx_line].split('\t')
                sent.append(content_part[0].lower())
                tag.append(content_part[1])
                temp = content_part[0].lower(),content_part[1]
                temp_test.append(temp)
            idx_line = idx_line + 1
        sentences.append(sent)
        tags.append(tag)
        alltest.append(temp_test)
        idx_line = idx_line + 2
    return sentences, alltest

test_word, test_tags = read_dataset2('Indonesian_Manually_Tagged_Corpus_ID_Viterbi_Test.tsv')

def read_file_init_table(fname):
    tag_count = {}
    tag_count['<start>'] = 0
    word_tag = {}
    tag_trans = {}
    with open(fname) as f:
        content = f.readlines()
    # you may also want to remove whitespace characters like `\n` at the end of each line
    content = [x.strip() for x in content]
    idx_line = 0
    is_first_word = 0

    while idx_line < len(content):
        prev_tag = '<start>'
        while not (content[idx_line].startswith('</kalimat')):
            if not content[idx_line].startswith('<kalimat'):
                content_part = content[idx_line].split('\t')
                if content_part[1] in tag_count:
                    tag_count[content_part[1]] += 1
                else:
                    tag_count[content_part[1]] = 1

                current_word_tag = content_part[0] + ',' + content_part[1]
                if current_word_tag in word_tag:
                    word_tag[current_word_tag] += 1
                else:
                    word_tag[current_word_tag] = 1

                if is_first_word == 1:
                    current_tag_trans = '<start>,' + content_part[1]
                    is_first_word = 0
                else:
                    current_tag_trans = prev_tag + ',' + content_part[1]

                if current_tag_trans in tag_trans:
                    tag_trans[current_tag_trans] += 1
                else:
                    tag_trans[current_tag_trans] = 1
                prev_tag = content_part[1]

            else:
                tag_count['<start>'] += 1
                is_first_word = 1
            idx_line = idx_line + 1

        idx_line = idx_line + 1
    return tag_count, word_tag, tag_trans

tag_count, word_tag, tag_trans = read_file_init_table('Indonesian_Manually_Tagged_Corpus_ID_Viterbi_Training.tsv')

def create_trans_prob_table(tag_trans, tag_count):
    trans_prob = {}
    for tag1 in tag_count.keys():
        for tag2 in tag_count.keys():
            trans_idx = tag1+','+tag2
            if trans_idx in tag_trans:
                trans_prob[tag1,tag2] = tag_trans[trans_idx]/tag_count[tag1] #frekuensi <start>,A / frekuensi <start>
    return trans_prob

trans_prob = create_trans_prob_table(tag_trans, tag_count)

def create_emission_prob_table(word_tag, tag_count):
    emission_prob = {}

    for word_tag_entry in word_tag.keys():
        try :
            if (word_tag_entry != ',,Z'):
                word_tag_split = word_tag_entry.split(',')
                current_word = word_tag_split[0].lower()
                current_tag = word_tag_split[1]
                emission_prob[current_word,current_tag] = word_tag[word_tag_entry]/tag_count[current_tag] #frekuensi saya,A / frekuensi tag A
            else :
                emission_prob[current_word,current_tag] = word_tag[',,Z'] / tag_count['Z']
        except :
            word_tag_split = word_tag_entry.replace(',','.',1).split(',') # merubah kata train yang memiliki koma 2 kali yang menyebabakan error . ex: 11,6,CD menjadi 11.6,CD
            current_word = word_tag_split[0].replace('.',',') # menjadi 11,6
            current_tag = word_tag_split[1] # menjadi CD
            emission_prob[current_word,current_tag] = word_tag[word_tag_entry]/tag_count[current_tag] # Dimasukan kedalam emission_prob

    return emission_prob

emission_prob = create_emission_prob_table(word_tag, tag_count)

#===================================================================================
def akurasi(allcontent, test_tag):
    count = 0
    for i in allcontent:
        for j in test_tag:
            if (i == j):
                count += 1
                break

    print("Benar : ", count, " / ", len(test_tag))
    print("Total : ", len(allcontent))

    return ((count/len(allcontent)) * 100)

def cariTag(temp_tag, tag): # fungsi yang digunakan untuk menentukan apakah kata test mempunyai lebi dari satu tag atau tidak
    cek = False

    for i in range(len(temp_tag)):
        if (temp_tag[i][1] == tag):
            cek = True
            break

    return cek

def cariTransition(trans_prob, tag_transition): # fungsi yang digunakan untuk menentukan apakah ada atau tidaknya trasisi dari kata sebelumnya ke kata selanjutnya
    cek = False

    if (tag_transition) in trans_prob.keys():
        cek = True

    return cek

def viterbi(trans_prob, emission_prob, sentence):
    tag_sequence = []
    test_tag_in_dataset = []
    temp_hasil_Viterbi = []

    for i in range(len(sentence)):
        for j in alltag:
            if (sentence[i], j) in emission_prob.keys():
                if (len(test_tag_in_dataset) == 0):
                    temp = sentence[i],j
                    test_tag_in_dataset.append(temp)
                elif not cariTag(test_tag_in_dataset, j):
                    temp = sentence[i], j
                    test_tag_in_dataset.append(temp)
        #========================================================= Mencari tag kata test dari tag kata train
        if (i == 0): #================= ketika kata pertama
            if (len(test_tag_in_dataset) != 0):
                if (len(test_tag_in_dataset) > 1): # ketika tag kata test memiliki lebih dari satu tag
                    for k in range(len(test_tag_in_dataset)):
                        temp = '<start>',test_tag_in_dataset[k][1] # test_tag_in_dataset merupakan kata test yang akan diuji
                        if (cariTransition(trans_prob,temp)): # pengecekan transition dari var temp apakah ada atau tidak
                            temp_hasil_Viterbi.append(emission_prob[test_tag_in_dataset[k]] * trans_prob[temp]) # memasukan nilai perkalian transition dan emission dari kata test yang memiliki lebih dari satu tag
                        else :
                            temp_hasil_Viterbi.append(0) # jika trasition dari '<start>' to 'test_tag_in_dataset' = 0 atau tidak ada
                    maxValue = max(temp_hasil_Viterbi) # menyimpan nilai tag yang tertinggi dari hasil perkalian trasition dan emission dari tag kata test
                    maxIndex = temp_hasil_Viterbi.index(max(temp_hasil_Viterbi)) # memberikan index list dari maxValue
                    tag_sequence.append(test_tag_in_dataset[maxIndex]) # memasukan tag yang memiliki value tertinggi dari maxValue bedasarkan index dari maxIndex
                else : # ketika tag kata test memiliki satu kata tag
                    temp = '<start>',test_tag_in_dataset[0][1]
                    if (cariTransition(trans_prob, temp)):
                        temp_hasil_Viterbi.append(emission_prob[test_tag_in_dataset[0]] * trans_prob[temp])
                    else:
                        temp_hasil_Viterbi.append(0)
                    maxValue = temp_hasil_Viterbi[len(temp_hasil_Viterbi)-1] # menyimpan nilai hasil perkalian dari transition dan emission
                    tag_sequence.append(test_tag_in_dataset[0]) # memasukan tag secara langsung ke tag_sequens
            else :
                temp = sentence[i], (max(tag_count, key=lambda i: tag_count[i])) # memasukan tag yang paling banyak dari tag kata train kepada kata test yang tidak memiliki tag bedasarkan kata train
                tag_sequence.append(temp)
        else : # =================== kata selanjutnya algoritma dibawah mirip seperti algoritam ketika kata pertama
            if (len(test_tag_in_dataset) != 0):
                if (len(test_tag_in_dataset) > 1):
                    for k in range(len(test_tag_in_dataset)):
                        temp = tag_sequence[len(tag_sequence)-1][1],test_tag_in_dataset[k][1] # tag sebelumnya di tag sequence digunakan untuk melakukan pengecekan transition_prob
                        if (cariTransition(trans_prob,temp)):
                            temp_hasil_Viterbi.append(maxValue * emission_prob[test_tag_in_dataset[k]] * trans_prob[temp])
                        else :
                            temp_hasil_Viterbi.append(0)
                    maxValue = max(temp_hasil_Viterbi)
                    maxIndex = temp_hasil_Viterbi.index(max(temp_hasil_Viterbi))
                    tag_sequence.append(test_tag_in_dataset[maxIndex])
                else :
                    temp = tag_sequence[len(tag_sequence)-1][1],test_tag_in_dataset[0][1]
                    if (cariTransition(trans_prob, temp)):
                        temp_hasil_Viterbi.append(maxValue * emission_prob[test_tag_in_dataset[0]] * trans_prob[temp])
                    else:
                        temp_hasil_Viterbi.append(0)
                    maxValue = temp_hasil_Viterbi[len(temp_hasil_Viterbi)-1]
                    tag_sequence.append(test_tag_in_dataset[0])
            else :
                temp = sentence[i],(max(tag_count, key=lambda i: tag_count[i]))
                tag_sequence.append(temp)
        # print(test_tag_in_dataset)
        # print(temp_hasil_Viterbi)
        # print()
        temp_hasil_Viterbi = [] # hasil perhitungan kata set di set menjadi null kembali setelah kata test di masukan ke tag sequence
        test_tag_in_dataset = [] # tag kata set di set menjadi null kembali setelah kata test di masukan ke tag sequence

    return tag_sequence

for i in range(len(test_word)):
    hasil = viterbi(trans_prob, emission_prob, test_word[i])
    print("Aktual Tagging : ", test_tags[i])
    print("Prediksi Tagging : ", hasil)
    print("Akurasi : ", akurasi(test_tags[i],hasil))
    print("================================================================================================================== Viterbi Method")
    print()