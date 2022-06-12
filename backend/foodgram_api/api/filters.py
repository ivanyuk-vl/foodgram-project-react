from rest_framework.filters import SearchFilter


class NameSearchFilter(SearchFilter):
    search_param = 'name'

    def get_search_fields(self, view, request):
        return ('^name',)
