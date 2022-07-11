import chalk from 'chalk';
import {
  COMPARISON_KEY,
  FILENAME_COMPARISON,
  FILENAME_SINGLE,
  generateFile,
  getComparisonDataPath,
  getEmbeddedIndexHTML,
  getFileData,
  log,
  PATH_TO_E2E_DATA_JSON,
  PATH_TO_INDEX,
  PATH_TO_SINGLE_REPORT_DATA_JSON,
  SINGLE_KEY,
} from './core.js';

/**
 * Inserts piperider report data into public/index.html
 * Note: This is for DEVELOPMENT ONLY. Make sure to exclude/revert index.html changes before pushing and committing!
 */

const insertDataToHTML = async () => {
  const reportDataMap = new Map();
  const isE2E = process.argv[2] === 'e2e';
  const datasetName = process.argv[3];

  if (isE2E && !datasetName) {
    return log(
      chalk.red(
        `Please provide a dataset name for your ${PATH_TO_E2E_DATA_JSON}/<DS_NAME>
        Example: npm run embed:html e2e <DS_NAME>
        `,
      ),
    );
  }

  // Read Report Data (Comparison/Single)

  // Declared here since this is dynamic
  const NEW_PATH_TO_COMPARISON_REPORT_DATA_JSON = isE2E
    ? `${PATH_TO_E2E_DATA_JSON}/${datasetName}/${FILENAME_COMPARISON}`
    : await getComparisonDataPath();
  const NEW_PATH_TO_SINGLE_REPORT_DATA_JSON = isE2E
    ? `${PATH_TO_E2E_DATA_JSON}/${datasetName}/${FILENAME_SINGLE}`
    : PATH_TO_SINGLE_REPORT_DATA_JSON;

  const argSetPaths = {
    [SINGLE_KEY]: NEW_PATH_TO_SINGLE_REPORT_DATA_JSON,
    [COMPARISON_KEY]: NEW_PATH_TO_COMPARISON_REPORT_DATA_JSON,
  };

  await setMapValues(reportDataMap, argSetPaths[SINGLE_KEY], SINGLE_KEY);

  await setMapValues(
    reportDataMap,
    argSetPaths[COMPARISON_KEY],
    COMPARISON_KEY,
  );

  // Embed Report Data to HTML and Rewrite
  const embedHtml = await getEmbeddedIndexHTML(reportDataMap);
  await generateFile(PATH_TO_INDEX, embedHtml.toString());
};

const setMapValues = async (dataMap, pathToReport, reportType) => {
  const jsonDataComparison = await getFileData(pathToReport);
  dataMap.set(reportType, jsonDataComparison);

  log(chalk.yellow(`Loading data from:${pathToReport}`));
};

insertDataToHTML();
