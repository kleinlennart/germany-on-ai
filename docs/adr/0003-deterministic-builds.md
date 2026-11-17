# Deterministic builds; model outputs are committed artefacts

The same commit must always produce byte-identical exports. Any output from a language model is generated once, committed with its model, prompt version and parameters, and read at build time instead of being regenerated. Model outputs vary between runs, and a public record whose numbers shift on rebuild cannot be cited or audited.
