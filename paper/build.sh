#!/bin/sh
# Builds main.pdf (named, for preprints) and main_anon.pdf (double-blind review).
set -e
cd "$(dirname "$0")"
tectonic main.tex
sed -e 's/\\author{.*}/\\author{\\IEEEauthorblockN{Anonymous Author(s)}}/' \
    -e '/\\IEEEauthorblockA{Independent Researcher/,/abhishekst5703@gmail.com}}/d' \
    -e 's#https://github.com/abhishek572003/iac-agent-security#https://anonymous.4open.science/r/iac-agent-security#' \
    -e 's/The author used an AI assistant/The authors used an AI assistant/; s/checked by the author, who takes/checked by the authors, who take/; s/reviewed by the author, who agreed/reviewed by the authors, who agreed/; s/by the author, who agreed/by the authors, who agreed/' \
    main.tex > main_anon.tex
tectonic main_anon.tex
echo "built main.pdf and main_anon.pdf"
