from setuptools import setup
from Cython.Build import cythonize
import numpy

setup(
    name='news_ingestion_optimized',
    ext_modules=cythonize([
        "extract_article_cy.pyx",
        "bucket_news_cy.pyx",
        "db_operations_cy.pyx",
        "text_processing_cy.pyx",
    ], 
    compiler_directives={
        'language_level': "3",
        'boundscheck': False,
        'wraparound': False,
        'initializedcheck': False,
        'cdivision': True,
    }),
    include_dirs=[numpy.get_include()],
    zip_safe=False,
)

