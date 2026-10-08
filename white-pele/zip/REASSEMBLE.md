# Reassembling the production ZIP

The ZIP is split into parts under 25 MB (23 MiB each).

```sh
cat White_Pele_production.zip.part* > White_Pele_production.zip     # the parts in order: part00, part01, ...
sha256sum -c FULL_SHA256                                             # check the whole ZIP
unzip White_Pele_production.zip                                      # -> episode/, library-overlay/, setup.sh, README.md, stills/
./setup.sh                                                           # rebuilds the editable project
```

On Windows: `copy /b White_Pele_production.zip.part00+White_Pele_production.zip.part01+... White_Pele_production.zip`.
`SHA256SUMS` checks each part on its own.
