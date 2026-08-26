class RAGService:
    def create_chunks(self, text: str):
        size = 1000
        overlap = 100
        return [text[i:i+size] for i in range(0, len(text), size-overlap)]

    async def get_context(self, question: str, office_id: str):

        query_filter = {'office_id: office_id'}
        return "Texto recuperado com segurança"
    