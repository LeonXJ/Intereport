"""IR sentence
"""

__author__      = 'leonxj@gmail.com (Jialiang Xie)'
__date__        = '2014-3-6'
__reviewer__    = 'leonxj@gmail.com (Jialiang Xie)'
__review_date__ = '2014-3-18'

class IRSentence(object):
    """
    Representation of Sentence.
    """

    def __init__(self, text, bug_id = None):
        self.__text = text
        self.__bug_id = bug_id

        self.__termcount = None
        self.__tfidf = None

    def get_text(self):
        return self.__text

    def get_bug_id(self):
        return self.__bug_id

    def get_termcount(self):
        if self.__termcount is None:
            from ir_term_count import IRTermCount
            self.__termcount = \
                IRTermCount.get_bow(self.get_text(), True)
        return self.__termcount

    def contain_term(self, term):
        if self.get_termcount().has_key(term):
            return True
        else:
            return False

    def get_tfidf(self):
        if self.__tfidf is None:
            from ir_config import IRConfig
            from ir_mongodb_helper import IRMongodbHelper
            from ir_tfidf import IRTFIDF
            description_name = IRConfig.get_instance().get('bug_description_name')
            tfidf_collection = IRMongodbHelper.get_instance().get_collection(
                'bug_db_name', 'bug_tfidf_collection_name', False)
            bug_count = tfidf_collection.count()
            
            self.__tfidf = \
                    IRTFIDF.calculate_tfidf(self.get_termcount(),
                                            description_name, bug_count, None, 'tfidf')
        return self.__tfidf

    @classmethod
    def get_sentence_from_description(cls, description, bug_id = None):
        """Generate sentences from description.

        Args:
            description: str
            bug_id: int

        Returns:
            [[ArIRSentence]
        """
        
        import re
        sentences = []
        sentences_text = re.split('\.[ \n]|\n\n', description)
        for text in sentences_text:
            text.replace('\n', ' ')
            sentences.append(IRSentence(text, bug_id))
        return sentences

    @classmethod
    def cluster_sentences(cls, sentences, n):
        """Cluster the sentences into n clusters.

        Args:
            sentences: [IRSentence]
            n: int, number of clusters

        Returns:
            [int], group id of each sentence in sentences
        """

        vol = set()
        for sentence in sentences:
            tfidf = sentence.get_tfidf()
            for term in tfidf:
                vol.add(term)
        vol = list(vol)
        vecs = []
        for sentence in sentences:
            tfidf = sentence.get_tfidf()
            vec = []
            for term in vol:
                if term in tfidf:
                    vec.append(tfidf[term])
                else:
                    vec.append(0.0)
            vecs.append(vec)
        # call pycluster k-means
        from Pycluster import kcluster, clustercentroids, distancematrix
        labels, error, nfound = kcluster(vecs, nclusters=n, method='a',
                                         dist='u')
        centroids, cmask = clustercentroids(vecs, clusterid=labels, method='a')
        sentence_ids = []
        for centroid_index, centroid in enumerate(centroids):
            # find vecs in the cluster
            subvecs = [centroid]
            subvecindexs = [-1]
            for label_index, label in enumerate(labels):
                if label == centroid_index:
                    subvecs.append(vecs[label_index])
                    subvecindexs.append(label_index)
            # find the min dist vec
            matrix = distancematrix(subvecs, dist='u')
            minimum = 100000
            minimum_index = 0
            for i in xrange(1, subvecs.__len__()):
                dist = matrix[i][0]
                if dist < minimum:
                    minimum = dist
                    minimum_index = subvecindexs[i]
            sentence_ids.append(minimum_index)

        # method='a')
        return labels, sentence_ids
        # return index of sentences, sentence of ids
