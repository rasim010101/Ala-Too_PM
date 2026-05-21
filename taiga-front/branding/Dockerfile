# Ala-Too PM frontend image.
#
# The official taigaio/taiga-front image already contains the compiled
# AngularJS bundle. We layer brand assets on top, rewrite the page title,
# inject our stylesheet override, and ship a config template that nginx
# substitutes at container start.
#
# Layout inside the base image (as of the digest we pin against):
#
#     /usr/share/nginx/html/
#         index.html
#         conf.json.template
#         v-<build-id>/
#             locales/taiga/locale-en.json
#             styles/theme-taiga.css
#             svg/logo-nav.svg
#
# The <build-id> changes on every upstream release, so we resolve it at
# build time instead of hard-coding it.

FROM taigaio/taiga-front:latest

WORKDIR /usr/share/nginx/html

# Stage our brand assets at a known path so the next RUN can move them
# into the versioned asset directory once it has resolved its name.
COPY branding/locale-en.json              /brand/locale-en.json
COPY branding/theme-alatoo-overrides.css  /brand/theme-alatoo-overrides.css
COPY branding/logo.svg                    /brand/logo.svg
COPY branding/favicon.png                 /brand/favicon.png
COPY branding/logo-alatoo.png             /brand/logo-alatoo.png
COPY branding/conf.json.template          /brand/conf.json.template

RUN set -eux; \
    VDIR="$(ls -d v-* | head -n1)"; \
    test -n "$VDIR"; \
    echo "Versioned asset dir: $VDIR"; \
    # 1) Brand strings in the document <head>.
    sed -i 's#<title>Taiga</title>#<title>Ala-Too PM</title>#' index.html; \
    sed -i 's#Taiga is a project management platform for startups and agile developers &amp; designers who want a simple, beautiful tool that makes work truly enjoyable.#Ala-Too PM is the project management workspace for Ala-Too International University courses, theses and lab work.#' index.html; \
    sed -i 's#<meta name="keywords" content="agile, scrum, taiga, management, project, developer, designer, user experience">#<meta name="keywords" content="ala-too, alatoo, university, agile, scrum, project management, courses">#' index.html; \
    # 2) Inject our overrides stylesheet right after the theme link.
    sed -i "s#<link rel=\"stylesheet\" href=\"${VDIR}/styles/theme-taiga.css\">#<link rel=\"stylesheet\" href=\"${VDIR}/styles/theme-taiga.css\"><link rel=\"stylesheet\" href=\"${VDIR}/styles/theme-alatoo-overrides.css\">#" index.html; \
    # 3) Place brand assets where index.html expects to find them.
    cp /brand/locale-en.json             "${VDIR}/locales/taiga/locale-en.json"; \
    cp /brand/theme-alatoo-overrides.css "${VDIR}/styles/theme-alatoo-overrides.css"; \
    # Overwrite the existing favicon.png (index.html already points at it,
    # so no html edit is needed) with the university seal.
    cp /brand/favicon.png                "${VDIR}/images/favicon.png"; \
    # Stash the raw PNG too — the CSS overrides reference it by URL for
    # the page-top university banner.
    cp /brand/logo-alatoo.png            "${VDIR}/images/logo-alatoo.png"; \
    # The same SVG wrapper is reused in three places: the navbar mark,
    # the large coloured mark on login/register/error screens, and the
    # plain mark used in modals. Overwriting all three keeps appearance
    # uniform across the app.
    cp /brand/logo.svg                   "${VDIR}/svg/logo-nav.svg"; \
    cp /brand/logo.svg                   "${VDIR}/svg/logo-color.svg"; \
    cp /brand/logo.svg                   "${VDIR}/svg/logo.svg"; \
    # 4) Replace the config template the entrypoint script substitutes.
    cp /brand/conf.json.template         conf.json.template; \
    cp /brand/conf.json.template         /conf.json.template; \
    rm -rf /brand
