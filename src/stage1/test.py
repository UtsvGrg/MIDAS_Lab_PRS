import torch, os
import torch.nn as nn
import fairseq
from torch.utils.data import DataLoader
from stage1MOS import MosPredictor, MyDataset
import numpy as np
import scipy.stats


ref = os.environ.get("REF")


## 1. load in pretrained model
device = torch.device("cuda" if torch.cuda.is_available() else "cpu")


cp_path = f'{ref}/table1_data/wav2vec_small.pt'
model, cfg, task = fairseq.checkpoint_utils.load_model_ensemble_and_task([cp_path])
ssl_model = model[0]
ssl_model.remove_pretraining_modules()

## running this on CPU-only generally does not work
model = MosPredictor(ssl_model).to(device)
model.eval()

print('Loading checkpoint')
my_checkpoint = 'checkpoints/my_MOS_SRCC'  #####
model.load_state_dict(torch.load(my_checkpoint))

print('Loading data')
wavdir = f'{ref}/table1_data/stage1MOS/train_test/DATA/wav'
validlist = f'{ref}/table1_data/stage1MOS/train_test/DATA/sets/test_mos_list.txt'
validset = MyDataset(wavdir, validlist)
validloader = DataLoader(validset, batch_size=1, shuffle=True, num_workers=2, collate_fn=validset.collate_fn)

total_loss = 0.0
num_steps = 0.0
predictions = { }  
criterion = torch.nn.MSELoss()

print('Starting prediction')
for i, data in enumerate(validloader, 0):
    inputs, labels, filenames = data
    inputs = inputs.to(device)
    labels = labels.to(device)

    # Features extraction
    inputs = inputs.squeeze(1)  ## [batches, audio_len]
    outputs = model(inputs)

    loss = criterion(outputs, labels)
    total_loss += loss.item()

    output = outputs.cpu().detach().numpy()[0]
    predictions[filenames[0]] = output

## compute correlations [utterance level]
## load in true labels
true_MOS = { }
validf = open(validlist, 'r')
for line in validf:
    parts = line.strip().split(',')
    uttID = parts[0]
    MOS = float(parts[1])
    true_MOS[uttID] = MOS

## compute correls.
sorted_uttIDs = sorted(predictions.keys())
ts = []
ps = []
for uttID in sorted_uttIDs:
    t = true_MOS[uttID]
    p = predictions[uttID]
    ts.append(t)
    ps.append(p)

truths = np.array(ts)
preds = np.array(ps)
    
### UTTERANCE
MSE=np.mean((truths-preds)**2)
print('[UTTERANCE] Test error= %f' % MSE)
LCC=np.corrcoef(truths, preds)
print('[UTTERANCE] Linear correlation coefficient= %f' % LCC[0][1])
SRCC=scipy.stats.spearmanr(truths.T, preds.T)
print('[UTTERANCE] Spearman rank correlation coefficient= %f' % SRCC[0])
KTAU=scipy.stats.kendalltau(truths, preds)
print('[UTTERANCE] Kendall Tau rank correlation coefficient= %f' % KTAU[0])

### SYSTEM
#sys_df = pd.read_csv('/home/smg/cooper/proj-mosnet-phase2/MOSNets/MOSNet-mydata-baseline/data/mydata_system.csv')
system_csv_path = '/home/smg/cooper/proj-mosnet-phase2/MOSNets/DATA/mydata_system.csv'
## remember keys maybe not all the same
true_sys_MOS_avg = { }
csv_file = open(system_csv_path, 'r')
csv_file.readline()  ## skip header
for line in csv_file:
    parts = line.strip().split(',')
    sysID = parts[0]
    MOS = float(parts[1])
    true_sys_MOS_avg[sysID] = MOS

def systemID(uttID):
    return uttID.split('-')[0] + '-' + uttID.split('-')[1]

pred_sys_MOSes = { }
for uttID in sorted_uttIDs:
    sysID = systemID(uttID)
    noop = pred_sys_MOSes.setdefault(sysID, [ ])
    pred_sys_MOSes[sysID].append(predictions[uttID])

pred_sys_MOS_avg = { }
for k, v in pred_sys_MOSes.items():
    avg_MOS = sum(v) / (len(v) * 1.0)
    pred_sys_MOS_avg[k] = avg_MOS

## make lists sorted by system
pred_sysIDs = sorted(pred_sys_MOS_avg.keys())
sys_p = [ ]
sys_t = [ ]
for sysID in pred_sysIDs:
    sys_p.append(pred_sys_MOS_avg[sysID])
    sys_t.append(true_sys_MOS_avg[sysID])

sys_true = np.array(sys_t)
sys_predicted = np.array(sys_p)

MSE=np.mean((sys_true-sys_predicted)**2)
print('[SYSTEM] Test error= %f' % MSE)
LCC=np.corrcoef(sys_true, sys_predicted)
print('[SYSTEM] Linear correlation coefficient= %f' % LCC[0][1])
SRCC=scipy.stats.spearmanr(sys_true.T, sys_predicted.T)
print('[SYSTEM] Spearman rank correlation coefficient= %f' % SRCC[0])
KTAU=scipy.stats.kendalltau(sys_true, sys_predicted)
print('[SYSTEM] Kendall Tau rank correlation coefficient= %f' % KTAU[0])

