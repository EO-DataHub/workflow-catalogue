cwlVersion: v1.0
$namespaces:
  s: https://schema.org/
$graph:
  - class: Workflow
    id: ndvi
    label: NDVI
    doc: Calculate NDVI for a STAC item
    inputs:
      stac_item:
        type: Directory
        doc: Staged STAC item
      bbox:
        type: string?
        doc: Bounding box as xmin,ymin,xmax,ymax
      dates:
        type: string[]
        doc: Start and end dates
    outputs:
      results:
        type: Directory
        outputSource: ndvi_step/results
    steps:
      ndvi_step:
        run: "#ndvi_tool"
        in:
          stac_item_dir: stac_item
          bbox_str: bbox
          date_list: dates
        out:
          - results
  - class: CommandLineTool
    id: ndvi_tool
    baseCommand: ["python", "/app/run.py"]
    inputs:
      stac_item_dir:
        type: Directory
        inputBinding:
          prefix: --stac-item
      bbox_str:
        type: string?
        inputBinding:
          prefix: --bbox
      date_list:
        type: string[]
        inputBinding:
          prefix: --dates
    outputs:
      results:
        type: Directory
        outputBinding:
          glob: .
