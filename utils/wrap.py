from typing import List, Type
import schemas.schemas as schemas

HOW_MANY_PREVIOUS_PAIRS = 5
WRAPPER_INIT = \
	"You are in the role of a chatbot in an ongoing conversation." \
	" The user is providing you with documents as sources and wants you to " \
	" consider only these provided sources when replying - you shall not " \
	" rely on general knowledge other than these 'Source facts' at the" \
	" bottom. The dialogue consists of pairs of (1) user queries and (2) " \
	"your responses. Consider these previous queries and responses" \
	" (if any) when replying to the 'new_query' below them:\n"


def convo_thus_far(
		all_convo_qa_pairs: List[Type[schemas.QAPair]],
		qa_pair_id: int
) -> str:
	"""Concatenate up to HOW_MANY_PREVIOUS_PAIRS, leading up to and including
	the QAPair with qa_pair_id, to the WRAPPER_INIT string before returning"""

	relevant_qa_pairs = []
	for old_qa_pair in all_convo_qa_pairs:
		if old_qa_pair.id <= qa_pair_id:
			relevant_qa_pairs.append(old_qa_pair)

	wrapper = WRAPPER_INIT
	for old_qa_pair in relevant_qa_pairs[-HOW_MANY_PREVIOUS_PAIRS::]:
		if not old_qa_pair.query or not old_qa_pair.response:
			continue
		wrapper += "previous_query: " + old_qa_pair.query
		wrapper += "previous_response: " + old_qa_pair.response
	wrapper += "new_query: "
	return wrapper
