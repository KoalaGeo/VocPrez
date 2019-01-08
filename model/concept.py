from pyldapi import Renderer, View
from flask import Response, render_template, url_for
import _config as config
import data.source as source
from rdflib import Graph, RDF, Literal, URIRef
from rdflib.namespace import SKOS, DCTERMS


class Concept:
    def __init__(
            self,
            vocab_id,
            uri,
            prefLabel,
            definition,
            altLabels,
            hiddenLabels,
            source,
            contributor,
            broaders,
            narrowers,
            semantic_properties
    ):
        self.vocab_id = vocab_id
        self.uri = uri
        self.prefLabel = prefLabel
        self.definition = definition
        self.altLabels = altLabels
        self.hiddenLabels = hiddenLabels
        self.source = source
        self.contributor = contributor
        self.broaders = broaders
        self.narrowers = narrowers
        self.semantic_properties = semantic_properties


class ConceptRenderer(Renderer):
    def __init__(self, request, concept):
        self.request = request
        self.views = self._add_views()
        self.navs = []  # TODO: add in other nav items for Concept

        self.concept = concept

        super().__init__(
            self.request,
            self.concept.uri,
            self.views,
            'skos'
        )

    def _add_views(self):
        return {
            'skos': View(
                'Simple Knowledge Organization System (SKOS)',
                'SKOS is a W3C recommendation designed for representation of thesauri, classification schemes, '
                'taxonomies, subject-heading systems, or any other type of structured controlled vocabulary.',
                ['text/html', 'application/json'] + self.RDF_MIMETYPES,
                'text/html',
                languages=['en'],  # default 'en' only for now
                namespace='http://www.w3.org/2004/02/skos/core#'
            )
        }

    def render(self):
        if self.view == 'alternates':
            return self._render_alternates_view()
        elif self.view == 'skos':
            if self.format in Renderer.RDF_MIMETYPES or self.format in Renderer.RDF_SERIALIZER_MAP:
                return self._render_skos_rdf()
            else:
                return self._render_skos_html()

    def _render_skos_rdf(self):
        # Create a graph from the self.concept object for a SKOS view
        s = URIRef(self.concept.uri)
        g = Graph()
        if self.concept.prefLabel:
            g.add((s, SKOS.prefLabel, Literal(self.concept.prefLabel)))
        if self.concept.definition:
            g.add((s, SKOS.definition, Literal(self.concept.definition)))
        if self.concept.altLabels:
            for label in self.concept.altLabels:
                g.add((s, SKOS.altLabel, Literal(label)))
        if self.concept.hiddenLabels:
            for label in self.concept.hiddenLabels:
                g.add((s, SKOS.hiddenLabel, Literal(label)))
        if self.concept.source:
            g.add((s, DCTERMS.source, Literal(self.concept.source)))
        if self.concept.contributor:
            g.add((s, DCTERMS.contributor, Literal(self.concept.contributor)))
        if self.concept.broaders: #
            g.add((s, SKOS.broader, Literal(self.concept.broaders)))
        if self.concept.narrowers:
            for n in self.concept.narrowers:
                g.add((s, SKOS.narrower, URIRef(n['uri'])))
                g.add((URIRef(n['uri']), SKOS.prefLabel, Literal(n['prefLabel'])))

        # serialise in the appropriate RDF format
        if self.format in ['application/rdf+json', 'application/json']:
            return Response(g.serialize(format='json-ld'), mimetype=self.format)
        else:
            return Response(g.serialize(format=self.format), mimetype=self.format)

    def _render_skos_html(self):
        _template_context = {
            'vocab_id': self.request.values.get('vocab_id'),
            'vocab_title': config.VOCABS[self.request.values.get('vocab_id')].get('title'),
            'uri': self.request.values.get('uri'),
            'concept': self.concept,
            'navs': self.navs
        }

        return Response(
            render_template(
                'concept.html',
                **_template_context
            ),
            headers=self.headers
        )

    def _render_alternates_view_html(self):
        my_context  = {
            'vocab_id': self.concept.vocab_id
        }
        return super(ConceptRenderer, self)._render_alternates_view_html(template_context=my_context)
    #     super().__init__(
    #         self.request,
    #         url_for('routes.object') + '?vocab_uri=' + self.concept.vocab_id,
    #         self.views,
    #         self.default_view_token
    #     )
