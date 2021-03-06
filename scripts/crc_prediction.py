#/usr/bin/python
import sys
import argparse
import numpy as np
from sklearn.externals import joblib

learning_algorithms = ['random_forest', 'svm', 'svr', 'neural_net', 'grad_boosting']

def parse_args(argv):
	parser = argparse.ArgumentParser(description="")
	parser.add_argument('-a', '--learning_algorithm', dest='learning_algorithm', default='random_forest', help='options: %s' % learning_algorithms)
	parser.add_argument('-i', '--input_expr', dest='input_expr')
	parser.add_argument('-f', '--input_expr_full', dest='input_expr_full')
	parser.add_argument('-p', '--outlier_predictors', dest='outlier_predictors')
	parser.add_argument('-s', '--normal_stats', dest='normal_stats')
	parser.add_argument('-m', '--model_filename', dest='model_filename')
	parser.add_argument('-v', '--verbose', dest='verbose', default=False)
	parsed = parser.parse_args(argv[1:])
	return parsed


def parse_data(filename, label_col, data_col_start):
	data = np.loadtxt(filename, dtype=str, delimiter='\t')
	gene_id = data[0, data_col_start:]
	sample_id = data[1:, 0]
	expr = np.array(data[1:, data_col_start:], dtype=np.float32)
	label = data[1:, label_col]
	return [gene_id, sample_id, expr, label]

def get_predictor_expr(filename, expr, gene_id):
	print expr.shape
	f = open(filename, "r")
	lines = f.readlines()
	tc_predictors_indx = []
	tc_predictors = []
	for line in lines:
		tmp_arr = line.strip().split("\t")
		if len(tmp_arr) > 1:
			for tmp_tc in tmp_arr[1].split(","):
				if tmp_tc in gene_id:
					tmp_indx = np.where(gene_id == tmp_tc)[0][0]
					tc_predictors_indx.append(tmp_indx)
					tc_predictors.append(tmp_tc)
	return (tc_predictors, expr[:, tc_predictors_indx])


def parse_normal_stats(filename):
	stats = np.loadtxt(filename, skiprows=1, dtype=str)
	stats_dict = {}
	for i in range(len(stats)):
		stats_dict[stats[i,0]] = [float(stats[i,3]), float(stats[i,4])]
	return stats_dict


def convert_labels(labels):
	conv_labels = -1 * np.ones(len(labels))
	for i in range(len(labels)):
		if labels[i] == 'N':
			conv_labels[i] = 0
		elif labels[i] == 'P':
			conv_labels[i] = 1
		elif labels[i] == 'C':
			conv_labels[i] = 2
	return conv_labels


def convert_reversed_labels(labels):
	conv_labels = np.chararray(len(labels))
	for i in range(len(labels)):
		if labels[i] < .5:
			conv_labels[i] = "N"
		elif labels[i] >= .5 and labels[i] < 1.5:
			conv_labels[i] = "P"
		elif labels[i] >= 1.5:
			conv_labels[i] = "C"
	return conv_labels


def calculate_confusion_matrix(label_te, label_pred):
	pred_pos = np.append(np.where(label_pred == "C")[0], np.where(label_pred == "P")[0])
	pred_neg = np.where(label_pred == "N")[0]
	te_pos = np.append(np.where(label_te == "C")[0], np.where(label_te == "P")[0])
	te_neg = np.where(label_te == "N")[0]
	tps = len(np.intersect1d(pred_pos, te_pos)) 
	fps = len(np.intersect1d(pred_pos, te_neg)) 
	fns = len(np.intersect1d(pred_neg, te_pos))
	tns = len(np.intersect1d(pred_neg, te_neg))
	print tps, fps, fns, tns
	sens = tps/float(len(te_pos))
	spec = tns/float(len(te_neg))
	accu = (tps+tns)/float(len(label_te))
	return [sens, spec, accu]


def main(argv):
	# parse data
	parsed = parse_args(argv)

	[gene_id, sample_id, expr_te, label_te] = parse_data(parsed.input_expr, 1, 2)
	[gene_id_full, foo, expr_te_full, foo] = parse_data(parsed.input_expr_full, 1, 2)

	label_unique= np.unique(label_te)
	label_count = np.array([len(np.where(label_te == l)[0]) for l in label_unique])

	print "Validation set dimension:", expr_te.shape[0], "samples x", expr_te.shape[1], "features"
	print "CRC labels:", label_unique, ", counts:", label_count 


	##### Random Forest #####
	if parsed.learning_algorithm.lower() ==	'random_forest':
		from sklearn.ensemble import RandomForestClassifier
		
		# predict on validation set
		clf = joblib.load(parsed.model_filename)
		label_predicted = clf.predict(expr_te)
		probability_predicted = clf.predict_proba(expr_te)
		accuracy_predicted = clf.score(expr_te, label_te)
		summary = np.hstack((sample_id[np.newaxis].T, label_te[np.newaxis].T, label_predicted[np.newaxis].T, probability_predicted))

		# print messages
		if parsed.verbose:
			print "sample_id\ttrue_label\tpredict_label\t", "\t".join(str(x) for x in clf.classes_)
			print '\n'.join('\t'.join(str(x) for x in row) for row in summary)
		# print "Prediction accuracy:", accuracy_predicted
		[sens, spec, accu] = calculate_confusion_matrix(label_te, label_predicted)
		print "Sens",sens, "Spec",spec, "Accu",accu


	##### SVM #####
	elif parsed.learning_algorithm.lower() == 'svm':
		from sklearn.svm import SVC

		# predict on validation set
		clf = joblib.load(parsed.model_filename)
		label_predicted = clf.predict(expr_te)
		probability_predicted = clf.predict_proba(expr_te)
		accuracy_predicted = clf.score(expr_te, label_te)
		summary = np.hstack((sample_id[np.newaxis].T, label_te[np.newaxis].T, label_predicted[np.newaxis].T, probability_predicted))

		# print message 
		if parsed.verbose:
			print "sample_id\ttrue_label\tpredict_label\t", "\t".join(str(x) for x in clf.classes_)
			print '\n'.join('\t'.join(str(x) for x in row) for row in summary)
		# print "Prediction accuracy:", accuracy_predicted
		[sens, spec, accu] = calculate_confusion_matrix(label_te, label_predicted)
		print "Sens",sens, "Spec",spec, "Accu",accu


	##### Nu-SVM #####
	elif parsed.learning_algorithm.lower() == 'nu_svm':
		from sklearn.svm import NuSVC

		# predict on validation set
		clf = joblib.load(parsed.model_filename)
		label_predicted = clf.predict(expr_te)
		probability_predicted = clf.predict_proba(expr_te)
		accuracy_predicted = clf.score(expr_te, label_te)
		summary = np.hstack((sample_id[np.newaxis].T, label_te[np.newaxis].T, label_predicted[np.newaxis].T, probability_predicted))

		# print message 
		if parsed.verbose:
			print "sample_id\ttrue_label\tpredict_label\t", "\t".join(str(x) for x in clf.classes_)
			print '\n'.join('\t'.join(str(x) for x in row) for row in summary)
		# print "Prediction accuracy:", accuracy_predicted
		[sens, spec, accu] = calculate_confusion_matrix(label_te, label_predicted)
		print "Sens",sens, "Spec",spec, "Accu",accu


	##### SVR #####
	elif parsed.learning_algorithm.lower() == 'svr':
		from sklearn.svm import SVR

		# predict on validation set
		clf = joblib.load(parsed.model_filename)
		label_predicted = clf.predict(expr_te)
		accuracy_predicted = clf.score(expr_te, convert_labels(label_te))
		summary = np.hstack((sample_id[np.newaxis].T, label_te[np.newaxis].T, convert_reversed_labels(label_predicted)[np.newaxis].T))

		# print message 
		if parsed.verbose:
			print "sample_id\ttrue_label\tpredict_label"
			print '\n'.join('\t'.join(str(x) for x in row) for row in summary)
		# print "Prediction accuracy:", accuracy_predicted
		[sens, spec, accu] = calculate_confusion_matrix(label_te, convert_reversed_labels(label_predicted))
		print "Sens",sens, "Spec",spec, "Accu",accu


	##### Neural Network #####
	elif parsed.learning_algorithm.lower() == 'neural_net':
		from sklearn.neural_network import BernoulliRBM

		# predict on validation set
		clf = joblib.load(parsed.model_filename)
		label_predicted = clf.predict(expr_te)
		accuracy_predicted = len([label_predicted[i] for i in range(len(label_predicted)) if (label_predicted[i] == label_te[i])]) / float(len(label_predicted))

		# print message 
		# print "Prediction accuracy:", accuracy_predicted
		[sens, spec, accu] = calculate_confusion_matrix(label_te, label_predicted)
		print "Sens",sens, "Spec",spec, "Accu",accu


	##### Gradient Boosting #####
	elif parsed.learning_algorithm.lower() == 'grad_boosting':
		from sklearn.ensemble import GradientBoostingClassifier
		
		# ## convert to two class
		# label_te = np.array([1 if x=='P' or x=='C' else 0 for x in label_te])

		# predict on validation set
		clf = joblib.load(parsed.model_filename)
		label_predicted = clf.predict(expr_te)
		probability_predicted = clf.predict_proba(expr_te)
		accuracy_predicted = clf.score(expr_te, label_te)
		summary = np.hstack((sample_id[np.newaxis].T, label_te[np.newaxis].T, label_predicted[np.newaxis].T, probability_predicted))

		# ## calculate score for ML prediction
		# score_ml = .8*clf.predict_proba(expr_te)[:,0]
		# ## add weight to outlier predictors
		# score_predictors = np.zeros(len(sample_id))
		# (tc_predictors, tc_predictors_expr) = get_predictor_expr(parsed.outlier_predictors, expr_te_full, gene_id_full)
		# weight_predictors = [.2/len(tc_predictors)]*len(tc_predictors)
		# tc_predictors_pct = parse_normal_stats(parsed.normal_stats)
		# for j in range(len(tc_predictors)):
		# 	pcts = tc_predictors_pct[tc_predictors[j]]
		# 	thld = 1*(pcts[1] - pcts[0]) + pcts[1]
		# 	indx = np.where(tc_predictors_expr[:,j] > thld)[0]
		# 	for i in indx:
		# 		score_predictors[i] += weight_predictors[j]
		# 		# score_predictors[i] = .2
		# ## final prediction
		# print("\t".join(["sample_id", "true_label", "predicted_label", "score_ML", "score_predictors", "final_score", "score_change?"]))
		# score_final = []
		# for i in range(len(sample_id)):
		# 	score = (score_ml[i]+score_predictors[i])/(1+score_predictors[i])
		# 	score_final.append(score)
		# 	predicted_label = "C" if score > .5 else "N"
		# 	print("\t".join( [sample_id[i], label_te[i], predicted_label, str(score_ml[i]), str(score_predictors[i]), str(score), str(score != score_ml[i])] ))

		#print messages
		if parsed.verbose:
			print "sample_id\ttrue_label\tpredict_label\t", "\t".join(str(x) for x in clf.classes_)
			print '\n'.join('\t'.join(str(x) for x in row) for row in summary)
		# print "Prediction accuracy:", accuracy_predicted
		[sens, spec, accu] = calculate_confusion_matrix(label_te, label_predicted)
		print "Sens",sens, "Spec",spec, "Accu",accu


	##### AdaBoost #####
	elif parsed.learning_algorithm.lower() == "adaboost":
		from sklearn.ensemble import AdaBoostClassifier
		from sklearn.tree import DecisionTreeClassifier

		# predict on validation set
		clf = joblib.load(parsed.model_filename)
		label_predicted = clf.predict(expr_te)
		probability_predicted = clf.predict_proba(expr_te)
		accuracy_predicted = clf.score(expr_te, label_te)
		summary = np.hstack((sample_id[np.newaxis].T, label_te[np.newaxis].T, label_predicted[np.newaxis].T, probability_predicted))
		
		#print messages
		if parsed.verbose:
			print "sample_id\ttrue_label\tpredict_label\t", "\t".join(str(x) for x in clf.classes_)
			print '\n'.join('\t'.join(str(x) for x in row) for row in summary)
		# print "Prediction accuracy:", accuracy_predicted
		[sens, spec, accu] = calculate_confusion_matrix(label_te, label_predicted)
		print "Sens",sens, "Spec",spec, "Accu",accu


	##### Gaussian Process #####
	elif parsed.learning_algorithm.lower() == 'gauss_process':
		from sklearn.gaussian_process import GaussianProcessClassifier
		from sklearn.gaussian_process.kernels import RBF
		
		# predict on validation set
		clf = joblib.load(parsed.model_filename)
		label_predicted = clf.predict(expr_te)
		probability_predicted = clf.predict_proba(expr_te)
		accuracy_predicted = clf.score(expr_te, label_te)
		summary = np.hstack((sample_id[np.newaxis].T, label_te[np.newaxis].T, label_predicted[np.newaxis].T, probability_predicted))

		# print messages
		if parsed.verbose:
			print "sample_id\ttrue_label\tpredict_label\t", "\t".join(str(x) for x in clf.classes_)
			print '\n'.join('\t'.join(str(x) for x in row) for row in summary)
		# print "Prediction accuracy:", accuracy_predicted
		[sens, spec, accu] = calculate_confusion_matrix(label_te, label_predicted)
		print "Sens",sens, "Spec",spec, "Accu",accu

	else:
		sys.exit('Improper learning algorithm option given.')

if __name__ == "__main__":
    main(sys.argv)

