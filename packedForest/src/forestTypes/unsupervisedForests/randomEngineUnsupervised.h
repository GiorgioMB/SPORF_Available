#ifndef randomEngineUnsupervised_h
#define randomEngineUnsupervised_h

#include <algorithm>
#include <cstdint>
#include <random>

namespace fp {

	// Random engine used by the unsupervised forests (URF and URerF).
	//
	// growTrees() in fpURFBase.h / fpURerFBase.h reseeds this engine at the
	// start of every tree with a seed drawn serially from the forest's seeded
	// generator. Each tree is grown entirely on one thread, so the forest
	// depends only on the "seed" parameter, not on the number of threads.
	inline std::mt19937& unsupervisedRandomEngine(){
		static thread_local std::mt19937 engine;
		return engine;
	}

	// Uniform integer in [low, high]. std::uniform_int_distribution and
	// std::shuffle use different algorithms in different standard libraries,
	// whereas std::mt19937 itself is fully specified, so these helpers give
	// the same results for the same seed on every platform.
	inline int unsupervisedRandomInt(int low, int high){
		const std::uint32_t span = static_cast<std::uint32_t>(high - low) + 1u;
		return low + static_cast<int>(static_cast<std::uint32_t>(unsupervisedRandomEngine()()) % span);
	}

	// Fisher-Yates shuffle driven by unsupervisedRandomInt.
	template <typename RandomIt>
	inline void unsupervisedShuffle(RandomIt first, RandomIt last){
		for(auto n = last - first; n > 1; --n){
			std::iter_swap(first + (n - 1), first + unsupervisedRandomInt(0, static_cast<int>(n - 1)));
		}
	}

}// namespace fp
#endif //randomEngineUnsupervised_h
