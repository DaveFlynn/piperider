import { SearchIcon } from '@chakra-ui/icons';
import { InputGroup, InputLeftElement, Input, Flex } from '@chakra-ui/react';
import { useState } from 'react';
import { AssertionStatusSummary } from '../components/shared/Assertions/AssertionStatusSummary';
import { Main } from '../components/shared/Layouts/Main';
import { AssertionListWidget } from '../components/shared/Widgets/AssertionListWidget';
import { useDocumentTitle, useAmplitudeOnMount } from '../hooks';
import { SaferSRSchema } from '../types';
import { AMPLITUDE_EVENTS, SR_TYPE_LABEL, useReportStore } from '../utils';
import { assertionListWidth } from '../utils/layout';

interface Props {
  data: SaferSRSchema;
}
export function SRAssertionListPage({ data }: Props) {
  useDocumentTitle('Single Report: Assertions');
  useAmplitudeOnMount({
    eventName: AMPLITUDE_EVENTS.PAGE_VIEW,
    eventProperties: {
      type: SR_TYPE_LABEL,
      page: 'assertion-list-page',
    },
  });
  const [filterString, setFilterString] = useState<string>('');
  const setRawReport = useReportStore((s) => s.setReportRawData);
  setRawReport({ base: data });
  const { tableColumnAssertionsOnly } = useReportStore.getState();

  return (
    <Main isSingleReport>
      <Flex w={'75%'} mt={10} ml={65} alignSelf={'start'}>
        <InputGroup my={2}>
          <InputLeftElement
            pointerEvents={'none'}
            children={<SearchIcon color={'gray.300'} />}
          />
          <Input
            bg={'white'}
            color={'black'}
            type={'text'}
            placeholder="Find By Assertion or Test Subject (Table, Column)"
            value={filterString}
            onChange={({ target }) => setFilterString(target.value)}
          />
        </InputGroup>
      </Flex>
      <AssertionStatusSummary
        p={5}
        w={assertionListWidth}
        failed={tableColumnAssertionsOnly?.metadata?.failed}
        passed={tableColumnAssertionsOnly?.metadata?.passed}
      />
      <AssertionListWidget
        w={assertionListWidth}
        singleOnly
        filterString={filterString}
        comparableAssertions={tableColumnAssertionsOnly}
      />
    </Main>
  );
}
