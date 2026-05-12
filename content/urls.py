from django.urls import re_path
from django.contrib.auth.views import LogoutView
from .views import (PublicHomeView, AboutCompanyView, NewsListView, NewsDetailView, FAQListView, PrivacyPolicyView,
                    VacancyListView, ReviewListView, PromoCodeListView,
                    CatalogListView, AddToCartView, CartView, RemoveFromCartView, ServiceManageListView,
                    ServiceCreateView, ServiceUpdateView, ServiceDeleteView)

app_name = 'content'

urlpatterns = [
    re_path(r'^$', PublicHomeView.as_view(), name='public_home'),
    re_path(r'^about/$', AboutCompanyView.as_view(), name='about_company'),
    re_path(r'^news/$', NewsListView.as_view(), name='news_list'),
    re_path(r'^news/(?P<pk>\d+)/$', NewsDetailView.as_view(), name='news_detail'),
    re_path(r'^faq/$', FAQListView.as_view(), name='faq_list'),
    re_path(r'^privacy-policy/$', PrivacyPolicyView.as_view(), name='privacy_policy'),
    re_path(r'^careers/$', VacancyListView.as_view(), name='vacancy_list'),
    re_path(r'^reviews/$', ReviewListView.as_view(), name='review_list'),
    re_path(r'^logout/$', LogoutView.as_view(next_page='/'), name='logout'),
    re_path(r'^promocodes/$', PromoCodeListView.as_view(), name='promo_list'),
    re_path(r'^catalog/$', CatalogListView.as_view(), name='catalog'),
    re_path(r'^add-to-cart/$', AddToCartView.as_view(), name='add_to_cart'),
    re_path(r'^cart/$', CartView.as_view(), name='cart'),
    re_path(r'^remove-from-cart/$', RemoveFromCartView.as_view(), name='remove_from_cart'),
    re_path(r'^manage/services/$', ServiceManageListView.as_view(), name='service_manage_list'),
    re_path(r'^manage/services/add/$', ServiceCreateView.as_view(), name='service_create'),
    re_path(r'^manage/services/(?P<pk>\d+)/edit/$', ServiceUpdateView.as_view(), name='service_update'),
    re_path(r'^manage/services/(?P<pk>\d+)/delete/$', ServiceDeleteView.as_view(), name='service_delete'),
]
