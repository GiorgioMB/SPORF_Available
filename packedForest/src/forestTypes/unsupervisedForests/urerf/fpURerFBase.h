#ifndef fpURerF_h
#define fpURerF_h

#include "../../../baseFunctions/fpForestBase.h"
#include <vector>
#include <map>
#include <algorithm>
#include <unordered_map>
#include <stdio.h>
#include <ctime>
#include <chrono>
#include <cstdlib>
#include "urerfTree.h"
#include <limits>
#include "../randomEngineUnsupervised.h"

namespace fp {
	template <typename T>
		class fpURerFBase : public fpForestBase<T>
	{
		protected:
			std::vector<urerfTree<T> > trees;
			std::map<int, std::map<int, int> > simMat;
                        std::map<std::pair<int, int>, double> pairMat;
		public:

			~fpURerFBase(){}

			fpDisplayProgress printProgress;
			inline void printForestType(){
				std::cout << "This is a urerf forest.\n";
			}

			inline void changeForestSize(){
				trees.resize(fpSingleton::getSingleton().returnNumTrees());
			}

			inline void initSimMat(){
				auto numObs = fpSingleton::getSingleton().returnNumObservations();
				for(auto i = 0; i < numObs; ++i) {
					std::map<int, int> init_map;
					simMat[i] = init_map;
				}
			}

			inline void growTrees(){
				// One seed per tree, drawn serially from the forest's seeded generator,
				// so the result depends only on the "seed" parameter.
				std::vector<int> treeSeeds(trees.size());
				for(auto& treeSeed : treeSeeds){
					treeSeed = fpSingleton::getSingleton().genRandom(std::numeric_limits<int>::max());
				}
#pragma omp parallel for num_threads(fpSingleton::getSingleton().returnNumThreads())
				for(int i = 0; i < (int)trees.size(); ++i){
					unsupervisedRandomEngine().seed(treeSeeds[i]);
					trees[i].growTree();
					trees[i].updateSimMat(simMat, pairMat);
					trees[i].updateSimMatOut(simMat, pairMat);
				}
			}


			inline void checkParameters(){
				//TODO: check parameters to make sure they make sense for this forest type.
				;
			}

			inline void treeStats(){
				int maxDepth=0;
				int totalLeafNodes=0;
				int totalLeafDepth=0;

				int tempMaxDepth;
				for(int i = 0; i < fpSingleton::getSingleton().returnNumTrees(); ++i){
					tempMaxDepth = trees[i].returnMaxDepth();
					maxDepth = ((maxDepth < tempMaxDepth) ? tempMaxDepth : maxDepth);

					totalLeafNodes += trees[i].returnNumLeafNodes();
					totalLeafDepth += trees[i].returnLeafDepthSum();
				}
			}


			inline std::map<int, std::map<int, int> > returnSimMat() {
				return simMat;
			}

			inline std::map<std::pair<int, int>, double> returnPairMat(){
                                        return pairMat;
                                }

			void printTree0(){
				trees[0].printTree();
			}

			void growForest(){
				changeForestSize();
				growTrees();
				treeStats();
			}

			inline int predictClass(std::vector<T> &observation)
			{
				std::cout << "Not implemented for unsupervised forests\n";
				return 0;
			}

			inline int predictClass(const T *observation)
			{
				std::cout << "Not implemented for unsupervised forests\n";
				return 0;
			}

			inline float reportOOB()
			{
				return 0;
			}
			
			inline std::vector<int> predictClassPost(std::vector<T> &observation)
			{
				std::cout << "Not implemented for unsupervised forests\n";
				return {};
			}

			inline float testForest()
			{
				return 0;
			}
	};

}// namespace fp
#endif
