export default function DeviceDetailPage({ id }) {
  return null;
}

export async function getServerSideProps(context) {
  return { props: { id: context.params.id } };
}
