import onnxruntime as ort
import numpy as np
import json

sess = ort.InferenceSession("web/model/student.onnx")
with open("web/model/labels.json") as f:
    labels = json.load(f)

with open("scratch/reference_32_classes.json") as f:
    ref_data = json.load(f)

correct = 0
confidences = []
margins = []
print(f"{'GLOSS':14s} | {'PREDICTED':14s} | {'PROB':6s} | {'MARGIN':6s} | {'STATUS'}")
print("-" * 55)

for gloss, seq in ref_data.items():
    inp = np.array(seq, dtype=np.float32)
    if inp.ndim == 3:
        inp = np.expand_dims(inp, 0)
    logits = sess.run(None, {"keypoints": inp})[0][0]
    probs = np.exp(logits - np.max(logits))
    probs /= probs.sum()
    top1 = int(np.argmax(probs))
    pred_gloss = labels[top1]
    top1_prob = float(probs[top1])
    sorted_probs = sorted(probs)
    margin = float(top1_prob - sorted_probs[-2])
    confidences.append(top1_prob)
    margins.append(margin)
    match = (pred_gloss == gloss)
    if match:
        correct += 1
    tag = "MATCH" if match else "DIFF"
    print(f"{gloss:14s} | {pred_gloss:14s} | {top1_prob:.4f} | {margin:.4f} | {tag}")

print("-" * 55)
print(f"Total Matches: {correct}/32 ({correct/32*100:.1f}%)")
print(f"Confidence Stats: Mean={np.mean(confidences):.4f}, Min={np.min(confidences):.4f}, Max={np.max(confidences):.4f}")
print(f"Margin Stats: Mean={np.mean(margins):.4f}, Min={np.min(margins):.4f}, Max={np.max(margins):.4f}")

