# ROI Naming Convention

**An ROI's name *is* its label.** Notebook 03 saves whatever you type in the
hsiViewer ROI panel into the `.pkl`, and the classifier parses the five training
labels straight back out of that string. A name that does not match the
convention is not rejected — it is silently labeled `N`, which means those pixels
train nothing. Getting the name right is the whole labeling step.

The convention is the one the ASD spectral library uses, so image ROIs and
library spectra land on the same classes. It is defined by
[`research_libMaker`](https://github.com/upwins/research_libMaker)
(`libMaker.py`), which builds the library, and consumed by
`upwins-veg-classifier` (`src/upwins_veg/roi_labels.py`).

## The pattern

```
<Genu_spe>_<PART>_<AGE>_<HEALTH>_<LIFECYCLE>
```

```
Ammo_bre_L_M_H_N          Ammophila breviligulata, leaf, mature, healthy, neither
Soli_sem_FL_M_H_FLG       Solidago sempervirens, flower, mature, healthy, flowering
Rosa_rug_MX_2G_DS_N       Rosa rugosa, mixed parts, year-2 growth, drought stressed
Genus_spe_MX_N_N_N        unidentified vegetation / background
```

You may append anything after the codes — a plot number, a date, a note. Extra
trailing text is ignored, as long as it does not itself look like a code.

## How the name is actually parsed

Four rules cause every mislabeling worth knowing about:

1. **The plant code must be the first 8 characters** (9 for `Genus_spe`) —
   4 letters of genus, `_`, 3 letters of species. It is matched
   **case-insensitively**, but it must be at the very *start* of the name.
   `Site1_Ammo_bre_L_M_H_N` matches no species and trains nothing on the plant
   head.
2. **The other four codes are matched as `_CODE_` tokens anywhere in the name,
   and are case-sensitive.** Position is convention, not enforcement — the
   parser finds `_FLG_` wherever it sits. But `_h_` is not `_H_`, and `_L` at
   the very end works only because a trailing `_` is appended for you.
3. **Use exactly one code per category.** If a name contains two codes from the
   same table, the later one in the table wins — quietly, and not in the order
   you wrote them.
4. **Anything unmatched becomes `N`.** For *part*, *age* and *health* that means
   the pixel is ignored for that task. For *lifecycle*, `N` ("Neither") is a
   real trained class. For *plant* it means the pixel trains no species at all;
   the training notebook prints a warning listing every name that fell through,
   so check that warning after your first run.

## The codes

**Plant** — `Genus_species` the model predicts:

| Code | Species | Common name |
|------|---------|-------------|
| `Ammo_bre` | *Ammophila breviligulata* | American Beachgrass |
| `Bacc_hal` | *Baccharis halimifolia* | Groundseltree |
| `Cham_fas` | *Chamaecrista fasciculata* | Partridge Pea |
| `Chas_lat` | *Chasmanthium latifolium* | River Oats |
| `Ilex_vom` | *Ilex vomitoria* | Yaupon Holly |
| `Iva_fru_` | *Iva frutescens* | Jesuit's Bark |
| `More_pen` | *Morella pennsylvanica* | Northern Bayberry |
| `Pani_ama` | *Panicum amarum* | Coastal Panic Grass |
| `Pani_vir` | *Panicum virgatum* | Switch Grass |
| `Robi_his` | *Robinia hispida* | Bristly Locust |
| `Rosa_rug` | *Rosa rugosa* | Sandy Beach Rose |
| `Soli_rug` | *Solidago rugosa* | Wrinkleleaf Goldenrod |
| `Soli_sem` | *Solidago sempervirens* | Seaside Goldenrod |
| `Genus_spe` | — | unidentified vegetation / background |

**Part** — which part of the plant the ROI covers:

| Code | Meaning |
|------|---------|
| `MX` | Mix |
| `L` | Leaf/Blade |
| `ST` | Internode Stem |
| `SP` | Sprout |
| `FL` | Flower |
| `FR` | Fruit |
| `SE` | Seed |
| `LG` | Lignin |

**Age:**

| Code | Meaning |
|------|---------|
| `PE` | Post-germination emergence |
| `1G` | Year 1 growth |
| `2G` | Year 2 growth |
| `J` | Juvenile |
| `M` | Mature |

**Health:**

| Code | Meaning |
|------|---------|
| `H` | Healthy |
| `S` | Stressed |
| `DS` | Drought stress |
| `SS` | Salt stress (soak) |
| `SY` | Salt stress (spray) |

**Lifecycle:**

| Code | Meaning |
|------|---------|
| `FLG` | Flowering |
| `FRG` | Fruiting |
| `FFG` | Fruiting and flowering |
| `D` | Dormant |
| `RE` | Re-emergence |
| `N` | Neither |

Note `FL` (part: flower) and `FLG` (lifecycle: flowering) are different codes,
as are `FR` (fruit) and `FRG` (fruiting). They are separate tokens and do not
collide, but they are easy to transpose.

### Accepted alternate spellings

These are recognized and folded into another class, so an older ROI still loads
correctly. Prefer the canonical code above for new ROIs:

| You type | Trains as |
|----------|-----------|
| `B` | `L` (Leaf/Blade) |
| `SA` | `ST` (Internode Stem) |
| `CS`, `RS` | `SP` (Sprout) |
| `E` | `PE` (Post-germination emergence) |
| `Iva_frut` | `Iva_fru_` (*Iva frutescens*) |

## What to name the `.pkl` file

The ROI *name* carries the labels; the *file* name carries one thing that
matters. A path containing **`crisfield`** or **`piloted`** (case-insensitive,
anywhere in the path) marks the ROIs as piloted-platform data, and the
classifier pixel-wise normalizes those spectra. Include the word for piloted
collects and leave it out otherwise — the same spectra normalized the wrong way
train a different model.

Beyond that, name the file after the collection. Everything under the
configured ROI directory is loaded recursively, so subfolders per collection
are fine.

## Reuse names across collections

The classifier pools every ROI file it finds into one training set, from this
repo and from `upwins-microscene-preprocessing` alike. `Soli_sem_L_M_H_N` must
mean the same thing in every collection, or the same class is trained on two
different things.

## Cal-panel ROIs are exempt

The calibration ROIs in notebook 01 are not training data and do not follow this
convention. They must be named exactly `Cal Panel Mid` and `Cal Panel Low` —
notebook 01 matches those literal strings.

## Checklist

- [ ] Name starts with the 8-character plant code, nothing before it.
- [ ] Codes are uppercase and underscore-separated.
- [ ] One code per category, in the order part, age, health, lifecycle.
- [ ] The same class name is spelled the same way as in past collections.
- [ ] `crisfield` / `piloted` in the file path if — and only if — that is the source.
- [ ] After the first training run, the "matched no key in plant_codes" warning is empty.
