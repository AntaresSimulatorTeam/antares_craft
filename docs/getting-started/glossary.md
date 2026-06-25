# Glossary

Here is a list of terms that are useful for understanding the `antares_craft`
package. For parameters meaning, explanations of modelization check Antares
[documentation](https://antares-doc.readthedocs.io/en/latest/).

| Term | Definition |
|---|---|
| ID | An ID for an area, a cluster or a link corresponds to the sanitized name defined by the user in Antares Web user interface. The name is lowered and special characters not in `_`, `(`, `)`, `,`, `&`,  ` ` (space), `-` are removed. |
| matrix | You will sometimes find `matrix` in method names or arguments. It corresponds to a dataframe with at least one column. Each column corresponds to a time series, that is to say a Monte-Carlo year of generally 8760 hourly values. | 